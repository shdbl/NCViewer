"""绘图中间契约对象，隔离界面控件与渲染实现。"""
from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass
class PlotSpec:
    plot_type: str = "map"
    var_name: str | None = None
    projection: str = "PlateCarree"
    central_lon: float = 0.0
    central_lat: float = 0.0
    levels: int | None = None
    level_min: float | None = None
    level_max: float | None = None
    colormap: str = "RdYlBu"
    discrete: bool = False
    grid_on: bool = True
    grid_interval: float | None = None
    title: str = ""
    subtitle: str = ""
    xlabel: str = ""
    ylabel: str = ""
    show_colorbar: bool = True
    shading: bool = False
    line_color: str | None = None
    line_width: float = 1.0       # 等值线线宽
    label_color: str = "black"    # 等值线标注文字颜色
    contour_labels: bool = False   # 等值线上标注数值（Panoply Labels）
    label_size: float = 8.0        # 等值线标注字号
    footnote_left: str = ""        # 左下方脚注（Panoply Footnotes）
    footnote_center: str = ""      # 中间脚注
    footnote_right: str = ""       # 右下方脚注
    lon_min: float | None = None   # 地图经度范围（None=全图）
    lon_max: float | None = None
    lat_min: float | None = None   # 地图纬度范围（None=全图）
    lat_max: float | None = None
    # ---- Panoply SCALE（色标）----
    log_scale: bool = False        # 对数色标
    alpha: float = 1.0             # 填充透明度
    # ---- Panoply CONTOURS 样式 ----
    contour_style: str = "filled"  # filled / lines / both（等值线绘制方式）
    # ---- Panoply LABELS 排版 ----
    title_size: float = 12.0
    subtitle_size: float = 10.0
    footnote_size: float = 8.0
    # ---- CF grid_mapping（数据自身投影坐标，内部使用）----
    _grid_mapping: dict | None = None  # get_grid_mapping 返回的投影参数
    show_minmax: bool = False      # 图上标注数据 min-max
    # ---- Panoply GRID 线型 ----
    grid_line_style: str = "solid"  # solid / dashed / dotted
    # ---- Panoply STROKE（折线图）----
    line_style: str = "-"           # - / -- / -. / :
    # ---- 数据归一化（C7）----
    normalize: bool = False         # 归一化到 0-100
    # ---- 矢量场（M2 VECTORS，对齐 Panoply PanVectorControls）----
    vector_scale: float = 1.0        # 箭头整体缩放（length factor）
    vector_density: int = 1          # 额外抽稀倍数（向后兼容）
    vector_color: str = "black"      # 箭头颜色
    vector_style: str = "ARROW"      # ARROW / NONE / UPDOT（Panoply PanVectorStyle）
    vector_spacing: int = 100        # 箭头间隔 %（25-250，Panoply vector.spacing）
    vector_weight: int = 100         # 箭头线粗 %（Panoply vector.weight）
    vector_refvalue: float = 10.0    # 参考值：箭头长度的基准（Panoply vector.refvalue）
    vector_sample: bool = True       # 显示参考箭头（Panoply vector.sample）

    def as_dict(self) -> dict:
        """转换为可保存到 QSettings/JSON 的字典。"""
        return asdict(self)

    @classmethod
    def from_dict(cls, values: dict) -> "PlotSpec":
        """从字典恢复绘图契约，忽略未知字段。"""
        fields = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in values.items() if k in fields})


def spec_from_defaults(var_name: str) -> PlotSpec:
    """根据变量名称创建合理的 M1 默认绘图配置。"""
    return PlotSpec(var_name=var_name, title=var_name)
