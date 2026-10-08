"""NCViewer 数据层：使用 xarray 对 NetCDF 文件进行懒加载和切片。"""
from __future__ import annotations
from pathlib import Path
import xarray as xr


# 支持的格式后缀 → xarray engine
_SUPPORTED_SUFFIXES = {".nc", ".nc4", ".grb", ".grib", ".grb2", ".grib2"}
_NETCDF_SUFFIXES = {".nc", ".nc4"}
_GRIB_SUFFIXES = {".grb", ".grib", ".grb2", ".grib2"}
_FORMAT_LABEL = "NetCDF/GRIB"


def open_dataset(path: str | Path) -> xr.Dataset:
    """懒加载打开本地 NetCDF / GRIB 文件，并在 Dataset.attrs 中保留原始路径。

    - ``.nc/.nc4`` → xarray 默认 netcdf4 后端；
    - ``.grb/.grib/.grb2/.grib2`` → cfgrib 后端（需安装 cfgrib+eccodes）。
    """
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"找不到数据文件：{file_path}")
    suffix = file_path.suffix.lower()
    if suffix not in _SUPPORTED_SUFFIXES:
        raise ValueError(f"仅支持 {_FORMAT_LABEL} 文件（{'/'.join(sorted(_SUPPORTED_SUFFIXES))}）：{file_path}")
    try:
        if suffix in _GRIB_SUFFIXES:
            ds = xr.open_dataset(file_path, engine="cfgrib", decode_times=True)
        else:
            ds = xr.open_dataset(file_path, decode_times=True)
    except ValueError as exc:
        # cfgrib 缺失等后端错误给出可读提示
        if "unrecognized engine" in str(exc) or "cfgrib" in str(exc):
            raise ValueError("打开 GRIB 文件需要安装 cfgrib + eccodes 依赖") from exc
        raise
    ds.attrs.setdefault("_ncviewer_source_path", str(file_path))
    return ds


def describe_variables(ds: xr.Dataset) -> list[dict]:
    """列出数据集变量的维度、形状、坐标名、单位、长名称和缺测值。"""
    result = []
    for name, da in ds.variables.items():
        attrs = da.attrs
        encoding = da.encoding
        result.append({
            "name": name, "dims": tuple(da.dims), "shape": tuple(da.shape),
            "coords": [d for d in da.dims if d in ds.coords],
            "units": attrs.get("units"), "long_name": attrs.get("long_name"),
            "missing_value": attrs.get("missing_value", encoding.get("missing_value")),
            "_FillValue": attrs.get("_FillValue", encoding.get("_FillValue")),
        })
    return result


def describe_global_attrs(ds: xr.Dataset) -> dict:
    """返回数据集全局属性的浅拷贝。"""
    return dict(ds.attrs)


def get_time_info(ds: xr.Dataset, var: str) -> dict:
    """获取变量时间维名称、首末值、步长、日历和时间单位，兼容 cftime 日历。

    时间维识别优先级（含 GRIB 场景）：
    1. 变量维度中的 ``time``/``times``；
    2. 变量维度中的 ``valid_time``（GRIB 实际预报时刻，datetime64，优先于 step）；
    3. 变量维度中的 ``step``（GRIB 预报步数，timedelta64）；
    4. 数据集坐标中的 ``time``/``valid_time``（单时次 GRIB 标量坐标）。
    """
    if var not in ds:
        raise KeyError(f"变量不存在：{var}")
    da = ds[var]
    time_name = next((d for d in da.dims if d.lower() in {"time", "times"}), None)
    if time_name is None:
        time_name = next((d for d in da.dims if "time" in d.lower() and d != "valid_time"), None)
    if time_name is None:
        # GRIB 实际预报时刻（datetime64，人类可读）优先于 step（timedelta64 步数）
        time_name = next((d for d in da.dims if d == "valid_time"), None)
    if time_name is None:
        time_name = next((d for d in da.dims if d in {"step", "valid_time"}), None)
    if time_name is None:
        # 单时次 GRIB：time 是标量坐标不在变量维度里
        for cand in ("time", "valid_time"):
            if cand in ds.coords and ds[cand].ndim == 0:
                time_name = cand
                break
    if time_name is None:
        raise ValueError(f"变量 {var} 不包含可识别的时间维")
    coord = ds[time_name]
    values = coord.values
    if len(values) == 0:
        raise ValueError(f"时间坐标 {time_name} 为空")
    # GRIB step 是 timedelta64（步数），若有同 shape 的 valid_time（datetime64）辅助
    # 坐标则改用它做显示值（人类可读的实际预报时刻）
    display_dim = time_name
    if time_name == "step" and "valid_time" in ds.coords:
        vt = ds["valid_time"]
        if tuple(vt.dims) == (time_name,) or (vt.ndim == 0 and len(values) == 1):
            coord = vt
            values = vt.values
            display_dim = "valid_time"
    calendar = coord.attrs.get("calendar") or coord.encoding.get("calendar")
    if calendar is None and hasattr(values[0], "calendar"):
        calendar = values[0].calendar
    calendar = str(calendar or "standard")
    step = values[1] - values[0] if len(values) > 1 else None
    return {"dim": display_dim, "start": values[0], "end": values[-1], "step": step,
            "calendar": calendar, "units": coord.attrs.get("units") or coord.encoding.get("units")}


def slice_var(ds: xr.Dataset, var: str, dim_slices: dict[str, slice | int], method: str = "isel") -> xr.DataArray:
    """先按 isel/sel 切片，再加载结果，避免对大文件整变量读取。"""
    if var not in ds:
        raise KeyError(f"变量不存在：{var}")
    if method not in {"isel", "sel"}:
        raise ValueError("method 必须是 'isel' 或 'sel'")
    da = ds[var]
    missing = [d for d in dim_slices if d not in da.dims]
    if missing:
        raise ValueError(f"变量 {var} 不存在这些维度：{', '.join(missing)}；现有维度：{', '.join(da.dims)}")
    result = da.isel(dim_slices) if method == "isel" else da.sel(dim_slices)
    return result.load()


# ---------- 2D 辅助经纬度（curvilinear grid）识别 ----------

def _looks_like_lon(name: str) -> bool:
    """名字启发式：看起来像经度坐标变量。"""
    low = name.lower()
    return low in {"lon", "longitude", "grid_lon", "gridlon", "nav_lon"} or low.endswith("longitude")


def _looks_like_lat(name: str) -> bool:
    """名字启发式：看起来像纬度坐标变量。"""
    low = name.lower()
    return low in {"lat", "latitude", "grid_lat", "gridlat", "nav_lat"} or low.endswith("latitude")


def _has_stdname(da: xr.DataArray, std: str) -> bool:
    """坐标变量 standard_name 是否匹配 longitude/latitude。"""
    return str(da.attrs.get("standard_name", "")).lower() == std


def find_aux_lonlat(ds: xr.Dataset, var: str) -> tuple[str, str] | None:
    """查找变量的 2D 辅助经纬度坐标（curvilinear grid）。

    对应 Panoply 的 NcArrayLonLatAuxiliary2D 识别逻辑：
    1. 优先读变量的 CF ``coordinates`` 属性（``coordinates="lon lat"``）；
    2. 否则在数据集中按名字/单位启发式找一对 2D lon/lat 变量；
    3. 校验：lon/lat 都是 2D、形状一致、且维度被数据变量共享。

    返回 (lon_var, lat_var)，找不到返回 None。
    """
    if var not in ds:
        return None
    da = ds[var]
    candidates: list[tuple[str, str]] = []

    # 1) CF coordinates 属性
    attr = str(da.attrs.get("coordinates", "") or "").strip()
    tokens = [t for t in attr.split() if t]
    if tokens:
        lonv = next((t for t in tokens if _looks_like_lon(t)), None)
        latv = next((t for t in tokens if _looks_like_lat(t)), None)
        if lonv and latv and lonv in ds and latv in ds:
            candidates.append((lonv, latv))

    # 2) 名字/standard_name/单位启发式：数据集中所有 2D 变量里找 lon/lat
    if not candidates:
        lon2d = [n for n in ds.variables
                 if ds[n].ndim == 2 and (_looks_like_lon(n) or _has_stdname(ds[n], "longitude"))]
        lat2d = [n for n in ds.variables
                 if ds[n].ndim == 2 and (_looks_like_lat(n) or _has_stdname(ds[n], "latitude"))]
        if lon2d and lat2d:
            candidates.append((lon2d[0], lat2d[0]))

    # 3) 校验维度共享（lon/lat 的 (y,x) 必须都是数据变量的维）
    for lonv, latv in candidates:
        if _validate_aux_lonlat(ds, var, lonv, latv):
            return lonv, latv
    return None


def _validate_aux_lonlat(ds: xr.Dataset, var: str, lonv: str, latv: str) -> bool:
    """校验辅助经纬度变量：2D、形状一致、维度被数据变量共享。"""
    da = ds[var]
    lon = ds[lonv]
    lat = ds[latv]
    if lon.ndim != 2 or lat.ndim != 2:
        return False
    if tuple(lon.shape) != tuple(lat.shape):
        return False
    lon_dims = set(lon.dims)
    lat_dims = set(lat.dims)
    if lon_dims != lat_dims:
        return False
    # 两个维度都要被数据变量共享（或数据变量含它们）
    var_dims = set(da.dims)
    if not lon_dims.issubset(var_dims):
        return False
    return True


def get_aux_lonlat_arrays(ds: xr.Dataset, var: str) -> tuple[xr.DataArray, xr.DataArray] | None:
    """返回变量的 2D 辅助经纬度数组 (lon2d, lat2d)，用于绘图。"""
    found = find_aux_lonlat(ds, var)
    if found is None:
        return None
    lonv, latv = found
    return ds[lonv], ds[latv]


# ---------- CF grid_mapping（投影坐标网格）解析 ----------

def get_grid_mapping(ds: xr.Dataset, var: str) -> dict | None:
    """解析变量的 CF ``grid_mapping`` 属性（投影坐标网格）。

    对应 Panoply 的 NcArrayLonLatProjected 识别：变量带 grid_mapping 属性
    指向一个 crs 变量，该变量含 grid_mapping_name 及投影参数。

    返回参数 dict（含 grid_mapping_name），无投影映射返回 None。
    """
    if var not in ds:
        return None
    da = ds[var]
    gm = str(da.attrs.get("grid_mapping", "") or "").strip()
    if not gm or gm not in ds:
        return None
    crs_var = ds[gm]
    params = dict(crs_var.attrs)
    name = str(params.get("grid_mapping_name", "") or "").strip()
    if not name:
        return None
    params["grid_mapping_name"] = name
    params["_crs_var"] = gm
    # 数值化常见参数（字符串转 float）
    for key in ("longitude_of_projection_origin", "latitude_of_projection_origin",
                "longitude_of_central_meridian", "latitude_of_projection_origin",
                "standard_parallel", "standard_parallel1", "standard_parallel2",
                "straight_vertical_longitude_from_pole", "latitude_of_standard_parallel",
                "scale_factor_at_projection_origin", "false_easting", "false_northing",
                "semi_major_axis", "semi_minor_axis", "inverse_flattening",
                "earth_radius", "north_pole_grid_longitude", "north_pole_grid_latitude"):
        if key in params:
            try:
                params[key] = float(params[key])
            except (TypeError, ValueError):
                pass
    return params