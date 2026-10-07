"""NCViewer 时间工具，始终保留 cftime 对非标准日历的支持。"""
from __future__ import annotations
import datetime as _dt
import numpy as _np
import pandas as _pd
import cftime


def detect_calendar(time_coord) -> str:
    """从坐标属性或元素类型识别 standard、noleap、360_day 等日历。"""
    calendar = time_coord.attrs.get("calendar") or getattr(time_coord, "encoding", {}).get("calendar")
    values = time_coord.values
    if not calendar and len(values):
        calendar = getattr(values[0], "calendar", None)
    return str(calendar or "standard")


def time_index_to_strs(time_coord, fmt: str = "%Y-%m-%d") -> list[str]:
    """将 cftime/datetime/datetime64 时间坐标格式化为供界面显示的字符串列表。"""
    result = []
    for value in time_coord.values:
        if isinstance(value, (cftime.datetime, _dt.datetime, _dt.date)):
            result.append(value.strftime(fmt))
        elif isinstance(value, _np.datetime64):
            # numpy.datetime64 无 strftime：转 pandas Timestamp 再格式化
            ts = _pd.Timestamp(value)
            result.append(ts.strftime(fmt))
        else:
            result.append(str(value))
    return result


def make_time_slider_range(time_coord) -> tuple[str, str, str]:
    """返回时间滑块的起始字符串、结束字符串和步长描述。"""
    values = time_coord.values
    if not len(values):
        return "", "", "无数据"
    labels = time_index_to_strs(time_coord)
    if len(values) < 2:
        step = "单个时间点"
    else:
        delta = values[1] - values[0]
        step = f"步长 {delta}"
    return labels[0], labels[-1], step