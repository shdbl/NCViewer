# -*- coding: utf-8 -*-
"""GRIB 格式支持测试（v1.0 增量）：open_dataset/get_time_info/_var_type_text/_stem。

测试数据：cfgrib 官方样例（data/regular_ll_sfc.grib 单变量 2D、
multi_param_on_multi_dims.grib 多变量 4D 预报）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # 项目根

from ncviewer.core.dataset import open_dataset, get_time_info
from ncviewer.ui.datatree import _var_type_text, _stem

DATA = Path(__file__).resolve().parents[1] / "data"


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL") + f" | {name}" + (f" | {detail}" if detail else ""))
    if not cond:
        raise AssertionError(f"{name}: {detail}")


# ---- 1. open_dataset 打开单变量 GRIB ----
ds1 = open_dataset(DATA / "regular_ll_sfc.grib")
check("open 单变量 GRIB", "skt" in ds1.data_vars, f"vars={list(ds1.data_vars)}")
check("单变量 GRIB 维度", tuple(ds1["skt"].shape) == (37, 72), str(tuple(ds1["skt"].shape)))
check("保留 source 路径", "_ncviewer_source_path" in ds1.attrs)

# ---- 2. open_dataset 打开多变量 4D GRIB ----
ds2 = open_dataset(DATA / "multi_param_on_multi_dims.grib")
check("open 多变量 GRIB", set(ds2.data_vars) >= {"z", "t", "u"}, str(set(ds2.data_vars)))
check("多变量 4D 形状", tuple(ds2["z"].shape) == (4, 4, 37, 72), str(tuple(ds2["z"].shape)))

# ---- 3. 非法后缀拒绝 ----
try:
    open_dataset(DATA / "regular_ll_sfc.grib" / ".." / ".." / ".." / "NCViewer-项目文档.md")
    check("非法后缀拒绝", False, "应抛 ValueError")
except ValueError:
    check("非法后缀拒绝", True)
except Exception as exc:
    check("非法后缀拒绝", False, f"抛错类型不对 {type(exc).__name__}")

# ---- 4. get_time_info 识别 GRIB 时间轴（优先 valid_time 人类可读）----
info = get_time_info(ds2, "z")
check("GRIB 时间维识别为 valid_time", info["dim"] == "valid_time", f"dim={info['dim']}")
check("GRIB 时间维长度", len(ds2["step"]) == 4, str(len(ds2["step"])))
check("GRIB 时间可读", "2018" in str(info["start"]),
      f"start={info['start']} 应为 2018-04-04T12:00")

# ---- 5. _var_type_text 分类 GRIB 变量 ----
t_z = _var_type_text({"name": "z", "dims": ("step", "isobaricInhPa", "latitude", "longitude")})
check("GRIB 4D 分类为经纬度场·含时间", "经纬度场" in t_z and "含时间" in t_z, t_z)
t_skt = _var_type_text({"name": "skt", "dims": ("latitude", "longitude")})
check("GRIB 2D 分类为经纬度场", t_skt == "经纬度场", t_skt)

# ---- 6. _stem 去 GRIB 后缀 ----
check("_stem .grib", _stem("foo.grib") == "foo", _stem("foo.grib"))
check("_stem .grib2", _stem("bar.grib2") == "bar", _stem("bar.grib2"))
check("_stem .grb", _stem("baz.grb") == "baz", _stem("baz.grb"))
check("_stem .nc 不变", _stem("demo.nc") == "demo", _stem("demo.nc"))

print("\n全部 GRIB 测试通过")
