"""matplotlib/cartopy 纯渲染函数：函数接收 Figure，不负责创建窗口。

支持 Panoply 全部可设置项：色标范围/对数刻度/透明度/等值线样式(填充/线/两者)/
归一化/图上 min-max 标注/标签字号/网格线型/脚注左中右/经纬度范围/矢量场箭头。
"""
from __future__ import annotations
import os
import sys
import matplotlib
matplotlib.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Noto Sans CJK SC"]
matplotlib.rcParams["axes.unicode_minus"] = False
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, LogNorm
import cartopy.crs as ccrs

# ---- 离线海岸线数据：优先使用随包内置的 Natural Earth shapefiles ----
# 源码运行时定位到 ncviewer/data（cartopy 会在 data_dir 下自动拼 shapefiles/natural_earth）；
# PyInstaller 打包后定位到 _MEIPASS/ncviewer/data。这样用户无需联网下载海岸线
# （cartopy 0.26 包内已不含矢量海岸线）。
_NE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data")
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    _NE_DIR = os.path.join(sys._MEIPASS, "ncviewer", "data")
if os.path.isdir(os.path.join(_NE_DIR, "shapefiles", "natural_earth")):
    import cartopy as _cartopy
    _cartopy.config["data_dir"] = _NE_DIR

from .spec import PlotSpec

_PROJECTIONS = {"PlateCarree": ccrs.PlateCarree, "Robinson": ccrs.Robinson,
                "Mollweide": ccrs.Mollweide, "LambertConformal": ccrs.LambertConformal,
                "NorthPolarStereo": ccrs.NorthPolarStereo, "Mercator": ccrs.Mercator}

_GRID_STYLES = {"solid": "solid", "dashed": "--", "dotted": ":"}
_LINE_STYLES = {"-": "-", "--": "--", "-.": "-.", ":": ":"}


def _projection(spec):
    cls = _PROJECTIONS.get(spec.projection, ccrs.PlateCarree)
    kwargs = {}
    if spec.projection in {"PlateCarree", "Robinson", "Mollweide"}:
        kwargs["central_longitude"] = spec.central_lon
    elif spec.projection == "LambertConformal":
        kwargs.update(central_longitude=spec.central_lon, central_latitude=spec.central_lat)
    return cls(**kwargs)


def _globe(params: dict):
    """从 CF 投影参数构建 cartopy Globe（自定义球体/椭球）。"""
    try:
        if params.get("inverse_flattening") == 0.0 or params.get("semi_minor_axis") == params.get("semi_major_axis"):
            return ccrs.Globe(ellipse="sphere", semimajor_axis=params.get("semi_major_axis") or 6371228.0)
        if params.get("semi_major_axis"):
            return ccrs.Globe(ellipse=None, semimajor_axis=params["semi_major_axis"],
                              semiminor_axis=params.get("semi_minor_axis"))
    except Exception:
        pass
    return ccrs.Globe()


def _projected_crs(params: dict):
    """由 CF grid_mapping 参数构建数据自身的投影 CRS（源坐标系）。

    对应 Panoply NcArrayLonLatProjected 的投影分派。返回 cartopy CRS。
    """
    name = params.get("grid_mapping_name", "")
    globe = _globe(params)
    lon0 = params.get("longitude_of_projection_origin", params.get("longitude_of_central_meridian", 0.0))
    lat0 = params.get("latitude_of_projection_origin", 0.0)
    if name == "latitude_longitude":
        return ccrs.PlateCarree(central_longitude=lon0)
    if name == "lambert_azimuthal_equal_area":
        return ccrs.LambertAzimuthalEqualArea(central_longitude=lon0, central_latitude=lat0, globe=globe)
    if name == "lambert_conformal_conic":
        sp1 = params.get("standard_parallel1", params.get("standard_parallel", 33.0))
        sp2 = params.get("standard_parallel2", sp1)
        return ccrs.LambertConformal(central_longitude=lon0, central_latitude=lat0,
                                     standard_parallels=(sp1, sp2), globe=globe)
    if name == "mercator":
        return ccrs.Mercator(central_longitude=lon0, globe=globe)
    if name == "polar_stereographic":
        return ccrs.Stereographic(central_longitude=lon0, central_latitude=90.0, globe=globe)
    if name == "stereographic":
        return ccrs.Stereographic(central_longitude=lon0, central_latitude=lat0, globe=globe)
    if name == "transverse_mercator":
        return ccrs.TransverseMercator(central_longitude=lon0, central_latitude=lat0,
                                       false_easting=params.get("false_easting", 0.0),
                                       false_northing=params.get("false_northing", 0.0), globe=globe)
    if name == "albers_conical_equal_area":
        sp1 = params.get("standard_parallel1", params.get("standard_parallel", 33.0))
        sp2 = params.get("standard_parallel2", sp1)
        return ccrs.AlbersEqualArea(central_longitude=lon0, central_latitude=lat0,
                                    standard_parallels=(sp1, sp2), globe=globe)
    if name == "rotated_latitude_longitude":
        return ccrs.RotatedPole(pole_longitude=params.get("north_pole_grid_longitude", 0.0),
                                pole_latitude=params.get("north_pole_grid_latitude", 90.0), globe=globe)
    if name == "geostationary":
        return ccrs.Geostationary(central_longitude=lon0, satellite_height=params.get("perspective_point_height", 35785831.0), globe=globe)
    if name == "sinusoidal":
        return ccrs.Sinusoidal(central_longitude=lon0, globe=globe)
    if name == "utm":
        zone = int(params.get("utm_zone", 33))
        return ccrs.UTM(zone=zone, southern_hemisphere=bool(params.get("utm_south", False)), globe=globe)
    # 未知投影回退 PlateCarree
    return ccrs.PlateCarree()


def _projected_xy(data, params: dict):
    """从投影网格数据的 x/y 一维坐标构建 (x2d, y2d) 网格。"""
    x_dim = next((d for d in data.dims if d.lower() in {"x", "xc", "x_0", "projection_x_coordinate"}), None)
    y_dim = next((d for d in data.dims if d.lower() in {"y", "yc", "y_0", "projection_y_coordinate"}), None)
    if x_dim is None or y_dim is None:
        # 退回取非时间维的最后两个
        dims = [d for d in data.dims if "time" not in d.lower()]
        if len(dims) >= 2:
            y_dim, x_dim = dims[0], dims[1]
        else:
            return None
    if x_dim not in data.coords or y_dim not in data.coords:
        return None
    x = np.asarray(data.coords[x_dim].values, dtype=float)
    y = np.asarray(data.coords[y_dim].values, dtype=float)
    x2d, y2d = np.meshgrid(x, y)
    return x2d, y2d, x_dim, y_dim

def _lat_lon(data):
    lat = next((d for d in data.dims if d.lower() in {"lat", "latitude", "y"}), None)
    lon = next((d for d in data.dims if d.lower() in {"lon", "longitude", "x"}), None)
    if not lat or not lon:
        raise ValueError(f"无法识别经纬度维度，现有维度：{data.dims}")
    return lat, lon


def _aux_lon_lat(data):
    """检测 data 是否带 2D 辅助经纬度坐标（curvilinear grid）。

    返回 (lon2d, lat2d) 两个 2D DataArray，或 None。
    识别策略（按优先级）：
    1. data.coords 中存在 2D 且名字/standard_name 像 lon/lat 的坐标
       （如 lon(y,x)/lat(y,x)、nav_lon/nav_lat、grid_lon/grid_lat）；
    2. 解析 data 的 CF ``coordinates`` 属性指向的变量；
    3. 辅助坐标的维度是数据维的子集（数据可含 time 等额外维）。
    """
    if data.ndim < 2:
        return None
    lon2d = lat2d = None

    def _match_lon(name, da):
        low = name.lower()
        std = str(da.attrs.get("standard_name", "")).lower()
        return low in {"lon", "longitude", "grid_lon", "gridlon", "nav_lon"} or \
            "longitude" in std or low.endswith("longitude")

    def _match_lat(name, da):
        low = name.lower()
        std = str(da.attrs.get("standard_name", "")).lower()
        return low in {"lat", "latitude", "grid_lat", "gridlat", "nav_lat"} or \
            "latitude" in std or low.endswith("latitude")

    # 1) coords 里的 2D 候选
    for name, c in data.coords.items():
        if c.ndim != 2:
            continue
        if lon2d is None and _match_lon(name, c):
            lon2d = c
        elif lat2d is None and _match_lat(name, c):
            lat2d = c
    # 2) CF coordinates 属性
    if lon2d is None or lat2d is None:
        attr = str(data.attrs.get("coordinates", "") or "").strip()
        tokens = [t for t in attr.split() if t]
        for t in tokens:
            if t in data.coords:
                c = data.coords[t]
                if c.ndim != 2:
                    continue
                if lon2d is None and _match_lon(t, c):
                    lon2d = c
                elif lat2d is None and _match_lat(t, c):
                    lat2d = c
    if lon2d is None or lat2d is None:
        return None
    # 辅助坐标维度必须一致，且是数据维的子集
    cset = set(lon2d.dims)
    if cset != set(lat2d.dims) or not cset.issubset(set(data.dims)):
        return None
    return lon2d, lat2d


def _time_dim(data):
    """识别时间维度名称，兼容 time/times 及带 time 的自定义名称。"""
    return next(
        (d for d in data.dims if d.lower() in {"time", "times"}),
        next((d for d in data.dims if "time" in d.lower()), None),
    )


def _lat_dim(data):
    return next((d for d in data.dims if d.lower() in {"lat", "latitude", "y"}), None)


def _is_hovmoller(data) -> bool:
    """二维数据含时间和纬度维、且不含经度维时视为 Hovmöller 数据。"""
    if data.ndim != 2:
        return False
    return _time_dim(data) is not None and _lat_dim(data) is not None and not any(
        d.lower() in {"lon", "longitude", "x"} for d in data.dims
    )


def _time_labels(coord) -> list[str]:
    """将时间坐标转换为坐标轴可读标签，兼容 cftime。"""
    labels = []
    for value in coord.values:
        labels.append(value.strftime("%Y-%m-%d") if hasattr(value, "strftime") else str(value))
    return labels

def _to_2d(data, dims):
    extra = [d for d in data.dims if d not in dims]
    if extra:
        # 多余维度（例如 time/level）取第一个索引，避免绘图阶段整读数据。
        data = data.isel({d: 0 for d in extra})
    return data.transpose(*dims)

def _normalize(values, spec):
    """归一化到 0-100（C7）。"""
    if not getattr(spec, "normalize", False):
        return values
    arr = np.asarray(values, dtype=float)
    lo, hi = np.nanmin(arr), np.nanmax(arr)
    if hi <= lo:
        return arr
    return (arr - lo) / (hi - lo) * 100.0


def _levels(values, spec):
    finite = np.asarray(values)[np.isfinite(values)]
    if finite.size == 0:
        # 空数组/全 NaN：返回保底 0-1 区间，避免 linspace(nan,nan)
        return np.linspace(0, 1, max(2, int(spec.levels or 20) + 1))
    lo = spec.level_min if spec.level_min is not None else (float(np.min(finite)) if finite.size else 0)
    hi = spec.level_max if spec.level_max is not None else (float(np.max(finite)) if finite.size else 1)
    if hi <= lo:
        padding = max(abs(lo) * 1e-6, 1e-6)
        lo -= padding
        hi += padding
    n = spec.levels or 20
    return np.linspace(lo, hi, max(2, int(n) + 1))


def _norm(values, levels, spec):
    """构造色标归一化：离散 / 对数 / 线性。

    log_scale 与 discrete 互斥（对数刻度下离散等值线无意义）。
    """
    if getattr(spec, "log_scale", False) and spec.discrete:
        raise ValueError("对数刻度与离散等值线不能同时启用")
    if getattr(spec, "log_scale", False):
        v = np.asarray(values)
        v_pos = v[v > 0]
        if v_pos.size == 0:
            raise ValueError(f"对数刻度需要正值数据，当前范围：[{np.nanmin(v)}, {np.nanmax(v)}]")
        lo = spec.level_min if spec.level_min is not None else float(np.min(v_pos))
        hi = spec.level_max if spec.level_max is not None else float(np.max(v_pos))
        if lo <= 0:
            lo = float(np.min(v_pos))
        if hi <= lo:
            hi = lo * 10
        return LogNorm(vmin=lo, vmax=hi)
    if spec.discrete:
        return BoundaryNorm(levels, plt.get_cmap(spec.colormap).N)
    return None


def _contour_labels(ax, mesh, spec):
    """在等值线上标注数值（Panoply 的 Labels 控制）。

    为兼容 Matplotlib 3.11+，仅在真正的等值线（contour，非 contourf）上标注；
    若传入的是 contourf 集合，自动用透明线重建轮廓再标注。
    标注带白色光晕，避免与密集等值线/填充重叠时看不清。
    """
    if not spec.contour_labels:
        return
    target = mesh
    if getattr(mesh, "filled", True):
        # contourf 对象：先以不可见细线重建轮廓，避免 clabel 弃用告警
        try:
            levels = np.asarray(mesh.levels)
            target = ax.contour(mesh, levels=levels, linewidths=0.3, colors="none")
        except Exception:
            return
    try:
        import matplotlib.patheffects as pe
        ax.clabel(target, fontsize=spec.label_size, inline=True, fmt="%.1f",
                  colors=spec.label_color,
                  path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])
    except Exception:
        pass  # 某些网格类型不支持标注，静默忽略


def _draw_contour_lines(ax, lon, lat, values, levels, spec):
    """叠加等值线（Panoply Contour Style=LINES），颜色/线宽可设。"""
    if not spec.line_color:
        return None
    return ax.contour(lon, lat, values, levels=levels, colors=spec.line_color,
                      linewidths=spec.line_width, transform=ccrs.PlateCarree())


def _set_extent(ax, spec):
    """应用用户设置的经纬度范围（Panoply Map 的 Center on / 区域选择）。

    关键坑：cartopy 的 set_extent 用 -180~180 约定，把 >180 的经度值归一化后
    （如 [100, 200]）会误判成跨日期变更线 → 整图变全图。因此：
    - PlateCarree（默认投影）：直接用 set_xlim/set_ylim 设窗口，0-360 原生
      经度原样生效，用户输入什么范围就显示什么范围（含 70~358 这类宽带）；
    - 其它投影：把 0-360 范围归一化到 -180~180 再 set_extent，跨日期变更线
      时降级为归一化后的窄带（无法表达非连续范围）。
    """
    if None in (spec.lon_min, spec.lon_max, spec.lat_min, spec.lat_max):
        return
    lon_min, lon_max = spec.lon_min, spec.lon_max
    lat_min, lat_max = spec.lat_min, spec.lat_max
    if spec.projection == "NorthPolarStereo" and lat_min < 0:
        lat_min = max(0.0, lat_min)  # 北半球极射投影不允许南半球范围
    if spec.projection == "SouthPolarStereo" and lat_max > 0:
        lat_max = min(0.0, lat_max)
    try:
        if isinstance(ax.projection, ccrs.PlateCarree):
            # 0-360 原生：直接设窗口，绕开 set_extent 的经度归一化 bug
            ax.set_xlim(lon_min, lon_max)
            ax.set_ylim(lat_min, lat_max)
        else:
            # 其它投影：0-360 → -180~180（200 → -160），再 set_extent。
            # 全经度（如 0~360 或 -180~180）归一化后 [0,0] 零宽会导致
            # 极射投影范围错乱，此时只设纬度范围、经度交给投影自身。
            lon_span = (lon_max - lon_min) % 360
            if lon_span >= 355 or (lon_span == 0 and lon_max != lon_min):
                # 全经度（跨度≈360 或负跨 360）：只限制纬度
                nlat0 = max(lat_min, -90.0)
                nlat1 = min(lat_max, 90.0)
                if nlat0 < nlat1:
                    ax.set_extent([-180, 180, nlat0, nlat1],
                                  crs=ccrs.PlateCarree())
                return
            nmin = lon_min - 360 if lon_min > 180 else lon_min
            nmax = lon_max - 360 if lon_max > 180 else lon_max
            if nmin <= nmax:
                ax.set_extent([nmin, nmax, lat_min, lat_max],
                              crs=ccrs.PlateCarree())
    except Exception:
        pass  # 某些投影/极区范围不合法时静默忽略


def _footnotes(fig, spec):
    """在图形底部左/中/右绘制脚注（Panoply Footnotes 左中右）。"""
    left = getattr(spec, "footnote_left", "") or ""
    center = getattr(spec, "footnote_center", "") or ""
    right = getattr(spec, "footnote_right", "") or ""
    size = getattr(spec, "footnote_size", 8.0)
    color = "#57606a"
    if left:
        fig.text(0.02, 0.015, left, ha="left", va="bottom", fontsize=size, color=color)
    if center:
        fig.text(0.5, 0.015, center, ha="center", va="bottom", fontsize=size, color=color)
    if right:
        fig.text(0.98, 0.015, right, ha="right", va="bottom", fontsize=size, color=color)


def _minmax_note(ax, values, spec):
    """在图形角落标注数据 min/max（Panoply Labels 的 Show data min-max）。"""
    if not getattr(spec, "show_minmax", False):
        return
    finite = np.asarray(values)[np.isfinite(values)]
    if finite.size == 0:
        return
    text = f"min={np.min(finite):.4g}  max={np.max(finite):.4g}"
    ax.text(0.015, 0.985, text, transform=ax.transAxes, ha="left", va="top",
            fontsize=8, color="#57606a", bbox=dict(boxstyle="round,pad=0.3",
                                                   fc="white", ec="#d8dee6", alpha=0.85))


def _apply_titles(ax, fig, spec):
    """标题/副标题/脚注/min-max 统一排版（含字号）。"""
    if spec.title:
        ax.set_title(spec.title, fontsize=getattr(spec, "title_size", 12.0))
    if spec.subtitle:
        ax.text(0.5, 1.01, spec.subtitle, transform=ax.transAxes, ha="center",
                fontsize=getattr(spec, "subtitle_size", 10.0))
    _footnotes(fig, spec)


def _grid_lines(ax, spec, crs=None):
    """地图经纬网格（只画左/下标签，避免与 colorbar 遮挡）；线型可设。"""
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5,
                      linestyle=_GRID_STYLES.get(spec.grid_line_style, "solid"), crs=crs)
    gl.top_labels = False
    gl.right_labels = False
    if spec.grid_interval:
        import matplotlib.ticker as mticker
        gl.xlocator = mticker.MultipleLocator(spec.grid_interval)
        gl.ylocator = mticker.MultipleLocator(spec.grid_interval)
    return gl


def render_map(data, spec: PlotSpec, fig, ax=None):
    """在给定 Figure 上绘制经纬度 contourf 地图。

    ax 为 None 时自行创建单图；传入外部 ax 时用于子图/合并绘图。
    优先级：
    1. CF 投影网格（spec._grid_mapping，数据自身投影坐标 x/y）→ pcolormesh 直画；
    2. 2D 辅助经纬度坐标（curvilinear grid）→ pcolormesh 弯曲网格；
    3. 常规 1D 经纬度 contourf。
    """
    gm = getattr(spec, "_grid_mapping", None)
    if gm:
        r = _render_map_projected(data, spec, fig, ax, gm)
        if r is not None:
            return r
    aux = _aux_lon_lat(data)
    if aux is not None:
        return _render_map_aux(data, spec, fig, ax, *aux)
    lat_dim, lon_dim = _lat_lon(data)
    data = _to_2d(data, (lat_dim, lon_dim))
    lat = data[lat_dim].values; lon = data[lon_dim].values
    values = _normalize(data.values, spec)
    if ax is None:
        ax = fig.add_subplot(1, 1, 1, projection=_projection(spec))
    elif ax.projection is None:
        ax.set_projection(_projection(spec))
    levels = _levels(values, spec)
    norm = _norm(values, levels, spec)
    cmap = spec.colormap
    style = getattr(spec, "contour_style", "filled")
    mesh = None
    # 样式：filled/both 画填充；lines/both 画线
    if style in {"filled", "both"}:
        mesh = ax.contourf(lon, lat, values, levels=levels, cmap=cmap, norm=norm,
                           transform=ccrs.PlateCarree(), extend="both",
                           alpha=getattr(spec, "alpha", 1.0))
    if style in {"lines", "both"}:
        ln = ax.contour(lon, lat, values, levels=levels,
                        colors=spec.line_color or "black",
                        linewidths=spec.line_width, transform=ccrs.PlateCarree())
        _contour_labels(ax, ln, spec)
    elif mesh is not None:
        _contour_labels(ax, mesh, spec)
    ax.coastlines(linewidth=0.5)
    _set_extent(ax, spec)
    if spec.grid_on:
        _grid_lines(ax, spec)
    _minmax_note(ax, values, spec)
    _apply_titles(ax, fig, spec)
    if spec.show_colorbar and (mesh is not None or style == "lines"):
        if mesh is None:
            mesh = ax.contourf(lon, lat, values, levels=levels, cmap=cmap,
                               norm=norm, transform=ccrs.PlateCarree(),
                               extend="both", alpha=0.0)  # 仅作色标映射
        fig.colorbar(mesh, ax=ax, shrink=0.8)
    return fig


def _render_map_projected(data, spec: PlotSpec, fig, ax, params):
    """CF 投影坐标网格地图：用数据自身的投影坐标 x/y 直画（transform=源CRS）。

    对应 Panoply NcArrayLonLatProjected + NcGridderLonLatProjected：不反算经纬度，
    直接在投影坐标空间绘制，无弯曲网格变形。显示投影由 spec.projection 决定。
    """
    xy = _projected_xy(data, params)
    if xy is None:
        return None
    x2d, y2d, x_dim, y_dim = xy
    data = _to_2d(data, (y_dim, x_dim))
    values = _normalize(np.asarray(data.values, dtype=float), spec)
    if ax is None:
        ax = fig.add_subplot(1, 1, 1, projection=_projection(spec))
    elif ax.projection is None:
        ax.set_projection(_projection(spec))
    src_crs = _projected_crs(params)
    # 色标范围：应用用户设置的 level_min/level_max（与常规 render_map 一致）
    levels = _levels(values, spec)
    norm = _norm(values, levels, spec)
    pc_kw = {}
    if norm is not None:
        pc_kw["norm"] = norm
    else:
        pc_kw["vmin"], pc_kw["vmax"] = float(levels[0]), float(levels[-1])
    mesh = ax.pcolormesh(x2d, y2d, values, cmap=spec.colormap,
                         shading="auto", transform=src_crs,
                         alpha=getattr(spec, "alpha", 1.0), **pc_kw)
    ax.coastlines(linewidth=0.5)
    if spec.grid_on:
        # 经纬网格线始终用 PlateCarree（cartopy gridliner 只支持它标注刻度）
        _grid_lines(ax, spec, crs=ccrs.PlateCarree())
    _minmax_note(ax, values, spec)
    _apply_titles(ax, fig, spec)
    if spec.show_colorbar:
        fig.colorbar(mesh, ax=ax, shrink=0.8)
    return fig


def _render_map_aux(data, spec: PlotSpec, fig, ax, lon2d, lat2d):
    """2D 辅助经纬度（curvilinear grid）地图：pcolormesh 画弯曲网格。"""
    # 多余维（如 time）取第 0 个，避免 3D values；lon/lat 辅助坐标不随多余维变化
    vdims = [d for d in data.dims if d in lon2d.dims] or list(data.dims)
    data = _to_2d(data, vdims)
    values = _normalize(np.asarray(data.values, dtype=float), spec)
    # 维度对齐：数据值、lon2d、lat2d 维度顺序一致（按数据维 transpose 辅助坐标）
    lon2d = lon2d.transpose(*vdims)
    lat2d = lat2d.transpose(*vdims)
    lon = np.asarray(lon2d.values, dtype=float)
    lat = np.asarray(lat2d.values, dtype=float)
    if ax is None:
        ax = fig.add_subplot(1, 1, 1, projection=_projection(spec))
    elif ax.projection is None:
        ax.set_projection(_projection(spec))
    # 色标范围：应用用户设置的 level_min/level_max（与常规 render_map 一致）
    levels = _levels(values, spec)
    norm = _norm(values, levels, spec)
    pc_kw = {}
    if norm is not None:
        pc_kw["norm"] = norm
    else:
        pc_kw["vmin"], pc_kw["vmax"] = float(levels[0]), float(levels[-1])
    mesh = ax.pcolormesh(lon, lat, values, cmap=spec.colormap,
                         shading="auto", transform=ccrs.PlateCarree(),
                         alpha=getattr(spec, "alpha", 1.0), **pc_kw)
    ax.coastlines(linewidth=0.5)
    _set_extent(ax, spec)
    if spec.grid_on:
        _grid_lines(ax, spec)
    _minmax_note(ax, values, spec)
    _apply_titles(ax, fig, spec)
    if spec.show_colorbar:
        fig.colorbar(mesh, ax=ax, shrink=0.8)
    return fig


def render_vector(data, spec: PlotSpec, fig, ax=None):
    """矢量场箭头图（M2 VECTORS，需数据含 风速U + 风速V 分量或 u/v 坐标）。

    支持 2D 辅助经纬度坐标（curvilinear grid）：检测到 2D lon/lat 时用
    辅助坐标定位箭头，否则走常规 1D 经纬度。
    """
    ds = data
    u = ds.get("u") if hasattr(ds, "get") else None
    v = ds.get("v") if hasattr(ds, "get") else None
    if u is None or v is None:
        raise ValueError("矢量场需要 u / v 两个变量")
    if ax is None:
        ax = fig.add_subplot(1, 1, 1, projection=_projection(spec))
    elif ax.projection is None:
        ax.set_projection(_projection(spec))
    # 2D 辅助经纬度：用 lon/lat 定位箭头
    aux = _aux_lon_lat(u)
    if aux is not None:
        lon2d, lat2d = aux
        vdims = [d for d in u.dims if d in lon2d.dims]
        u2 = _to_2d(u, vdims)
        v2 = _to_2d(v, vdims)
        lon = np.asarray(lon2d.transpose(*vdims).values, dtype=float)
        lat = np.asarray(lat2d.transpose(*vdims).values, dtype=float)
    else:
        lat_dim, lon_dim = _lat_lon(u)
        u2 = _to_2d(u, (lat_dim, lon_dim))
        v2 = _to_2d(v, (lat_dim, lon_dim))
        lat = u2[lat_dim].values; lon = u2[lon_dim].values
    U = np.asarray(u2.values); V = np.asarray(v2.values)
    # ---- Panoply PanVectorControls 参数 ----
    style = (getattr(spec, "vector_style", "ARROW") or "ARROW").upper()
    if style == "NONE":
        q = None
    else:
        # 抽稀：自动目标（≈800 箭头，清爽可读）为基础步长，再按 Spacing(25-250%) 调整
        import math as _math
        density = max(1, int(getattr(spec, "vector_density", 1) or 1))
        ny, nx = U.shape
        base_step = max(1, _math.ceil((ny * nx / 800.0) ** 0.5))
        spacing = float(getattr(spec, "vector_spacing", 100) or 100)
        step = max(1, int(round(base_step * spacing / 100.0)), density)
        # 粗细：Weight(%) → quiver 箭头轴宽（默认 0.005 ≈ 100%）
        weight = float(getattr(spec, "vector_weight", 100) or 100)
        # 大小：Reference Value 越大箭头越短（Panoply vector.refvalue 语义）
        refvalue = float(getattr(spec, "vector_refvalue", 10.0) or 10.0)
        refvalue = max(refvalue, 0.1)
        vscale = float(getattr(spec, "vector_scale", 1.0) or 1.0)
        scale = max(1e-6, 100.0 * vscale * (10.0 / refvalue))
        q = ax.quiver(
            lon[::step], lat[::step], U[::step, ::step], V[::step, ::step],
            scale=scale, width=0.005 * (weight / 100.0),
            color=getattr(spec, "vector_color", "black"),
            transform=ccrs.PlateCarree(), alpha=getattr(spec, "alpha", 1.0),
            pivot="middle" if style == "UPDOT" else "tail", zorder=3,
        )
        if style == "UPDOT":
            # Upstream Dot：在箭头上游（起点）加点标记
            ax.scatter(lon[::step], lat[::step], s=2.5, marker="o",
                       color=getattr(spec, "vector_color", "black"),
                       transform=ccrs.PlateCarree(), zorder=4)
    # 海岸线：加粗并置于箭头之上，避免被密箭头盖住（用户反馈"地图没了"）
    ax.coastlines(linewidth=1.0, zorder=8)
    _set_extent(ax, spec)
    if spec.grid_on:
        _grid_lines(ax, spec)
    _minmax_note(ax, np.hypot(U, V), spec)
    _apply_titles(ax, fig, spec)
    # Scale Sample：显示参考箭头（Panoply vector.sample）
    if q is not None and getattr(spec, "vector_sample", True):
        try:
            ax.quiverkey(q, 0.92, 1.05, refvalue, f"{refvalue:g}",
                         labelpos="E", coordinates="axes",
                         fontproperties={"size": 8})
        except Exception:
            pass
    if spec.show_colorbar:
        pass
    return fig


_VECTOR_PAIRS = [
    ("u", "v"), ("U", "V"), ("x_wind", "y_wind"),
    ("uwnd", "vwnd"), ("u_wind", "v_wind"), ("eastward_wind", "northward_wind"),
    ("uice", "vice"), ("u_ice", "v_ice"), ("drift_u", "drift_v"),
]


def _vector_pair(names: list[str]) -> tuple[str, str] | None:
    """检测变量名列表是否构成矢量分量对（u/v、U/V、x_wind/y_wind 等）。

    返回 (u_name, v_name)，不构成对返回 None。大小写不敏感。
    """
    if not names or len(names) != 2:
        return None
    low = {n.lower() for n in names}
    for u, v in _VECTOR_PAIRS:
        if u.lower() in low and v.lower() in low:
            # 保持原始大小写返回
            un = next(n for n in names if n.lower() == u.lower())
            vn = next(n for n in names if n.lower() == v.lower())
            return un, vn
    return None


def render_line(data, spec: PlotSpec, fig, ax=None):
    """绘制一维折线图；多余维度取第一个索引。线型/线宽可设。"""
    while data.ndim > 1: data = data.isel({data.dims[0]: 0})
    if ax is None:
        ax = fig.add_subplot(1, 1, 1)
    x = data.coords[data.dims[0]].values if data.dims else np.arange(data.size)
    # cftime 的非标准日历对象不能直接转换为 matplotlib 浮点日期，
    # 因此使用等间隔索引绘制，并保留时间顺序供后续 UI 标注。
    if data.dims and x.size and not np.issubdtype(np.asarray(x).dtype, np.number):
        x = np.arange(data.size)
    values = _normalize(data.values, spec)
    ls = _LINE_STYLES.get(getattr(spec, "line_style", "-"), "-")
    ax.plot(x, values, color=spec.line_color or None,
            linestyle=ls, linewidth=getattr(spec, "line_width", 1.0))
    ax.set_title(spec.title or spec.var_name or "时间序列",
                 fontsize=getattr(spec, "title_size", 12.0))
    ax.set_xlabel(spec.xlabel); ax.set_ylabel(spec.ylabel)
    if spec.grid_on:
        ax.grid(True, linestyle=_GRID_STYLES.get(spec.grid_line_style, "solid"))
    _minmax_note(ax, values, spec)
    _footnotes(fig, spec)
    return fig


def render_contour(data, spec: PlotSpec, fig, ax=None):
    """绘制非地理二维数组等高线（ax 可外部传入用于子图）。"""
    while data.ndim > 2: data = data.isel({data.dims[0]: 0})
    if data.ndim != 2: raise ValueError("等高线图需要二维数据")
    values = _normalize(data.values, spec)  # 修正：contourf/contour 均用归一化后的值
    if ax is None:
        ax = fig.add_subplot(1, 1, 1)
    levels = _levels(values, spec)
    norm = _norm(values, levels, spec)
    cmap = spec.colormap
    style = getattr(spec, "contour_style", "filled")
    mesh = None
    if style in {"filled", "both"}:
        mesh = ax.contourf(values, levels=levels, cmap=cmap, norm=norm,
                           alpha=getattr(spec, "alpha", 1.0))
    if style in {"lines", "both"}:
        cs_lines = ax.contour(values, levels=levels,
                              colors=spec.line_color or "black",
                              linewidths=spec.line_width)
        _contour_labels(ax, cs_lines, spec)
    elif mesh is not None:
        _contour_labels(ax, mesh, spec)
    _minmax_note(ax, values, spec)
    if spec.show_colorbar:
        if mesh is None:
            mesh = ax.contourf(values, levels=levels, cmap=cmap, norm=norm, alpha=0.0)
        fig.colorbar(mesh, ax=ax)
    ax.set_title(spec.title or spec.var_name or "等高线图",
                 fontsize=getattr(spec, "title_size", 12.0))
    _footnotes(fig, spec)
    return fig


def render_hovmoller(data, spec: PlotSpec, fig, ax=None):
    """绘制时间-纬度 Hovmöller 剖面图。"""
    if not _is_hovmoller(data):
        raise ValueError("Hovmöller 图需要二维时间-纬度数据")
    time_dim = _time_dim(data)
    lat_dim = _lat_dim(data)
    data = data.transpose(time_dim, lat_dim)
    time_coord = data[time_dim]
    lat = np.asarray(data[lat_dim].values)
    values = _normalize(data.values, spec)
    x = np.arange(values.shape[0], dtype=float)
    if ax is None:
        ax = fig.add_subplot(1, 1, 1)
    levels = _levels(values, spec)
    norm = _norm(values, levels, spec)
    mesh = ax.contourf(x, lat, values.T, levels=levels, cmap=spec.colormap, norm=norm,
                       extend="both", alpha=getattr(spec, "alpha", 1.0))
    _contour_labels(ax, mesh, spec)
    labels = _time_labels(time_coord)
    if labels:
        max_ticks = 8
        tick_indices = np.unique(np.linspace(0, len(labels) - 1,
                                             min(max_ticks, len(labels)), dtype=int))
        ax.set_xticks(tick_indices)
        ax.set_xticklabels([labels[i] for i in tick_indices], rotation=30, ha="right")
    ax.set_title(spec.title or f"{spec.var_name or '变量'} 时间-纬度剖面",
                 fontsize=getattr(spec, "title_size", 12.0))
    ax.set_xlabel(spec.xlabel or "时间")
    ax.set_ylabel(spec.ylabel or "纬度")
    if spec.grid_on:
        ax.grid(True, linestyle=_GRID_STYLES.get(spec.grid_line_style, "solid"), linewidth=0.5, alpha=0.5)
    _minmax_note(ax, values, spec)
    if spec.show_colorbar:
        fig.colorbar(mesh, ax=ax)
    _footnotes(fig, spec)
    return fig


def render(data, spec: PlotSpec, fig, ax=None):
    """按 PlotSpec.plot_type 分派渲染函数，并自动识别时间-纬度剖面。

    ax 可外部传入（子图/合并绘图场景）；None 时各函数自行 add_subplot。
    """
    if spec.plot_type == "hovmoller":
        return render_hovmoller(data, spec, fig, ax)
    if _is_hovmoller(data):
        return render_hovmoller(data, spec, fig, ax)
    if spec.plot_type == "map": return render_map(data, spec, fig, ax)
    if spec.plot_type == "vector": return render_vector(data, spec, fig, ax)
    if spec.plot_type == "line": return render_line(data, spec, fig, ax)
    if spec.plot_type in {"contour", "contourf"}: return render_contour(data, spec, fig, ax)
    raise ValueError(f"不支持的绘图类型：{spec.plot_type}")
