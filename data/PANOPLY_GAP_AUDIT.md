# NCViewer 非常规网格数据差距审计报告

## 1. 结论摘要

按可独立复现的数据场景归并为 **8 项差距**，其中 **严重度=高 4 项**。高严重度集中在常见气象/卫星投影坐标和非规则全球网格：NCViewer 不读取 `grid_mapping` 并将投影坐标轴反算为地理坐标，也没有立方球、多面体或 UGRID 的单元拓扑绘制器；这类数据可能被错误判成普通等值线或因缺少 `lat/lon` 命名维而直接报错。优先补齐 CF 投影网格和有明确目标数据源的 GMAO/CAM-SE 立方球；UGRID、多面体需要完整拓扑/多边形绘制能力，投入较大，应作为独立功能评估。

中等差距为 3D 随层变化的辅助经纬度、Reduced grid 与已识别 2D curvilinear 的非地图绘图/坐标发现边界。常规 1D 经纬度及典型二维辅助经纬度地图路径已有支持，不计为整体差距；其中存在的限制单列为边界缺陷。

严重度含义：高=常见业务数据无法地理定位或整个拓扑无法表达；中=专门网格/剖面工作流缺失或只支持典型子集；低=有明显可绕过限制。本次没有列低项。

## 2. 差距清单

| 数据场景 | Panoply 检测条件（源码位置+简述） | Panoply 怎么画 | NCViewer 现状（支持/不支持/部分） | 差距严重度 | 实现建议 |
|---|---|---|---|---|---|
| CF 投影坐标网格（含 RotatedPole、GOES/MSG 特殊投影） | `NcVarTypeDetector.java:541-595` 按变量 `grid_mapping` 名称识别；`NcArrayFactory.java:153-199` 分派 14 种投影处理器 | `NcArrayLonLatProjected` 子类按映射参数生成轴；`NcGridderLonLatProjected` 转经纬度空间后栅格化 | 不支持：`render.py:34-39, 295-298` 只按维名 lat/lon 找轴；`plot_window.py:368-373` 对投影 x/y 判普通 contour | 高 | 读取 CF grid_mapping 和投影参数，建 Cartopy CRS/transform 并为 x/y 网格生成地理坐标 |
| GMAO / CAM-SE cubed-sphere 六面体网格 | `NcVarTypeDetector.java:498-501` 检测 GMAO 与 CAM-SE；`NcArrayLonLatCubedSphereGMAO.java:584-715`、同名 CAMSE 类 `canGridVariable` | 对 tile/face 维及各面坐标重排，`NcGridderLonLatCubedSphereGMAO/CAMSE` 转为经纬度图 | 不支持：无 face/tile 维识别；2D 网格渲染需要二维 lon/lat 坐标 | 高 | 先支持目标生产格式的 tile 坐标展开/拼接，再沿用经纬度网格渲染 |
| 球面多面体网格（ICOS/hexagon 等） | `NcVarTypeDetector.java:496-497`；`NcArrayLonLatPolyhedron.java:545-670` 验证多面体坐标拓扑 | `NcGridderLonLatPolyhedron` 将各多边形单元定位并栅格化 | 不支持：没有面片拓扑及多边形单元渲染；`pcolormesh` 路径只接收矩形二维数组 | 高 | 解析单元顶点/中心拓扑，以 PolyCollection/三角剖分或重采样到规则经纬网格绘制 |
| UGRID 非结构网格（face/edge） | `NcVarTypeDetector.java:519-538` 要求 UGRID-1.0、`mesh`、location；:486-495 选择 Faces/Edges；`NcArrayLonLatUgridFaces.java` / `...Edges.java` `canGridVariable` | 依据 mesh topology、node 坐标和 face/edge 连接关系，`NcGridderLonLatUgrid` 生成相应多边形/线单元 | 不支持：无 mesh/location/topology 消费逻辑，不能把不规则 face/edge 值映射到二维规则数组 | 高 | 实现 UGRID topology 解析和面/边几何绘制；只用 xarray 读取数据还不够，需要保留连接关系 |
| 3D 随垂直层变化的辅助经纬度 | `NcVarTypeDetector.java:504-505`；`NcArrayLonLatAuxiliary3D.java:85-153, 760-771` 接受 rank-3 坐标并构造轴 | 按当前垂直层切片同步选择 3D lon/lat，再用 `NcGridderLonLatAuxiliary` 映射 | 部分：`dataset.py:141-158` 与 `render.py:42-67` 仅接受 2D 坐标；3D 坐标会被拒绝/忽略，随后可能报维名错误或画非地理 contour | 中 | 先切片数据的 level/time，再用相同索引切片 lon/lat，保证坐标和数据完全对齐 |
| Reduced Gaussian / Reduced CF / Reduced ISCCP 降分辨率网格 | `NcVarTypeDetector.java:508-513` 顺序检测；对应 `NcArrayLonLatReducedCF.java:137-192`、`NcArrayLonLatReduced2D.java:786-842`、`NcArrayLonLatReducedISCCP.java:103` 起 | 按每纬圈不同列数/行起点解释压缩的一维或变长行数据，再由对应 `NcGridderLonLatReduced*` 映射 | 不支持：数组长度非规则二维，当前 `_lat_lon` 和地图渲染假设矩形二维值数组 | 中 | 识别 reduced row-count/row-start 元数据，按 cell bounds 展开或重采样到规则网格 |
| Curvilinear 2D 辅助坐标用于线/等值线/Hovmöller及坐标发现 | Panoply `NcArrayLonLatAuxiliary2D.java:71-138, 617-624` 从 coordinates/坐标变量检查；`NcArrayFactory.java:240-244` 选 2D/3D；PanData 类型保留经纬度轴 | `NcGridderLonLatAuxiliary` 对 2D lon/lat 网格化；地图及剖面绘图可沿地理轴使用坐标 | 部分/边界缺陷：地图 `_aux_lon_lat` 只遍历 `data.coords` 且名称限于 lon/longitude/grid_lon/gridlon 等（`render.py:42-67`）；`dataset.py:106-137` 的变量辅助发现没有被该渲染分派调用。line/contour 也不消费地理坐标（`render.py:433-487`），Hovmöller 只认一维纬度维（:82-88, 490-505） | 中 | 统一用 dataset 辅助坐标解析结果；对 curvilinear 场明确提供地理剖面/纬度带聚合，而非把二维经纬度压成普通线图 |
| 常规 2D 辅助经纬度格式边界（非标准变量名、维度次序/切片） | Panoply `NcArrayLonLatAuxiliary2D.java:71-138, 259-300, 617-624` 根据 CF coordinates、变量属性及坐标数组判断；`NcGridderLonLatAuxiliary.java` | 对有效 2D lon/lat 进行维度对齐后绘图 | 部分/边界缺陷：`dataset.py:107-113` 仅根据 coordinates 中的变量名词形匹配；启发式只取第一个 2D lon/lat（:115-137）。渲染器自身只扫描已成为 DataArray coords 的坐标，且依赖有限名称（`render.py:53-67`）；合法但非标准命名/未挂接为 coords 的 CF 辅助变量会漏检。`_render_map_aux` 会把不随 lon/lat 变化的多余维取第 0 项（:337-343） | 中 | 优先解析 CF `coordinates`、`standard_name`/units；验证所有候选坐标与数据维度、索引后再选取，避免静默取错坐标 |

## 3. 中/高严重度差距详述

### 3.1 CF 投影网格及旋转极

典型来源包括 WRF、COSMO/ICON 区域模式、GRIB 转 NetCDF 产品以及 GOES/MSG 卫星投影产品。Panoply 在 `NcVarTypeDetector.java:541-595` 从 `grid_mapping` 识别 Lambert Conformal、Mercator、Geostationary、RotatedPole、MSGNavigation、UTM 等映射，并在 `NcArrayFactory.java:153-199` 交给对应实现。NCViewer 当前的地图路径仅寻找名字为 lat/lon/latitude/longitude 的数据维（`render.py:34-39`）；即使 x/y 一维坐标及 `grid_mapping` 完整，`plot_window.py:368-373` 也会把它自动分为普通 contour，未做地图投影转换。因此可能仅显示无地理参考的轴，或在自动地图渲染时因缺少 lat/lon 维而抛出 `ValueError`，不能与海岸线正确叠加。

实现上应先解析变量的 CF `grid_mapping` 属性及映射变量参数，使用 Cartopy 对应 CRS 表达原生投影坐标；`transform` 指明源 CRS。若后续操作需要经纬度网格，则由 x/y meshgrid 执行 CRS 反投影；RotatedPole 使用旋转球面坐标转换。不能用变量名猜投影。

### 3.2 Cubed-sphere 六面体

典型来源是 NASA GEOS/GMAO 与 CAMS/CAM-SE 模式。Panoply 分别检查 GMAO/CAM-SE 格式（`NcVarTypeDetector.java:498-501`），数组类负责读取面/瓦片维并构造轴，随后 `NcGridderLonLatCubedSphereGMAO/CAMSE` 做空间重排。NCViewer 的 curvilinear 绘制器要求数据与二维 lon/lat 数组相配（`render.py:42-67, 335-352`），没有识别六面体 tile 面或拼缝的代码；单纯把六面当普通二维轴会产生错误布局，若额外维被当作非地图维则自动判图也可能落到普通 contour。

实现可针对某个明确定义的文件约定读取六面各自坐标，将 face 维分面投影或先重采样为公共经纬度网格；需显式处理面边界与重复/缺失格点，不能只 reshape。

### 3.3 多面体球面网格

典型来源包括全球非结构气候/海洋模型和 ICOS/多边形离散化数据。Panoply `NcArrayLonLatPolyhedron.java:545-670` 验证顶点/面拓扑，`NcGridderLonLatPolyhedron` 将单元作为多边形网格化。NCViewer 目前 `render_map` 到 `pcolormesh` 的输入为矩形数组（`render.py:335-352`），无法表达一个单元拥有不同数量的顶点；会无法识别或只能误当一般轴图。

xarray 可承载节点坐标和 connectivity，但需要读 connectivity 的填充值/索引基准并建立单元多边形。绘制可用 Matplotlib `PolyCollection` 配 Cartopy 投影，或先做保守/最近邻重网格；对于全球接缝和跨日期变更线单元，应拆分几何。

### 3.4 UGRID 面与边场

常见于 FVCOM、SCHISM、ADCIRC、三角网格海洋/水动力模型。Panoply 检查 `Conventions` 含 UGRID-1.0、变量 `mesh` 和 `location`（`NcVarTypeDetector.java:519-538`），Faces/Edges 通过专用数组类并由 `NcGridderLonLatUgrid` 用 mesh connectivity 处理。NCViewer 没有解析 mesh topology 变量，也没有 node-to-face/edge 连接映射；规则 `pcolormesh` 不能替代这一语义。通常不是普通变量绘图错误，而是不能提供地理场地图。

实现需沿 mesh topology 引用读取 node lon/lat、face_node_connectivity/edge_node_connectivity、start_index 和 `_FillValue`，按 location 把值关联到几何，并在 Cartopy 目标 CRS 中画多边形或线段。可先做 face 数据，再扩展 edge/node。

### 3.5 3D 辅助经纬度

典型场景是随高度/气压层变化的曲面坐标，例如地形跟随垂直坐标和部分卫星扫描/体积产品。Panoply 有独立 `NcArrayLonLatAuxiliary3D`（`NcVarTypeDetector.java:504-505`；`NcArrayLonLatAuxiliary3D.java:85-153`），在垂直切片时取对应坐标层。NCViewer 的验证要求 lon/lat `ndim == 2`（`dataset.py:146-153`），渲染辅助坐标也跳过非二维坐标（`render.py:53-55`），所以不匹配 2D 地理坐标路径，后续多半被判 contour 或因维度名称不对失败。

可将垂直维切片同步应用于数据、lon、lat，再复用现有二维 pcolormesh。若坐标还有 time 维，需确认切片维与数据所选索引一致。

### 3.6 Reduced grids

Reduced Gaussian 网格常见于 ECMWF/IFS 与 GRIB 产品；Reduced CF 和 ISCCP 格式也常用于气候及卫星辐射资料。Panoply 对三类分别检测并实例化数组（`NcVarTypeDetector.java:508-513`；`NcArrayFactory.java:258-265`）。由于各纬圈格点数不同，变量可能是压缩的一维序列或 row-length 编码，并非规则 `lat × lon` 矩形。NCViewer 的 `render_map` 需要经纬度维并把数据转为二维（`render.py:295-298`），不会按每行格点数拆分，无法正确绘图；强行 reshape 会造成行错位。

可读取行长度及 cell bounds，逐行恢复经纬度单元，或重采样至规则经纬网格。若只有点坐标，可先提供散点/三角网格显示并清楚标明重网格方式。

### 3.7 2D curvilinear 的非地图路径和发现边界（边界缺陷）

典型来源包括 WRF、COSMO 及卫星 swath。NCViewer 已有 `pcolormesh` 地图路径（`render.py:335-352`），但 `_aux_lon_lat` 仅检查 DataArray 的坐标对象及有限名称；另有 `dataset.py:91-167` 的 `find_aux_lonlat` 可以读 `coordinates` 属性和做维度校验，却没有被渲染器调用。于是合法 lon/lat 作为 Dataset data variables 而未附加到 DataArray coords 时，检测路径仍返回 None；非标准名字但带 CF `standard_name`/units 的辅助坐标也可能漏掉。自动类型选择随后依据维名（`plot_window.py:368-373`），可能落到 contour，数据维名为 y/x 时 `render_map` 还会因 `lat/lon` 维识别失败而报错。

此外，地图功能虽使用二维坐标，但 `render_line` 只画一维坐标曲线（`render.py:433-454`），`render_contour` 不传地理坐标（:457-487），Hovmöller 仅接受 time+一维纬度维（:82-88, 490-505）。因此不能把这些曲线/等值线场景算作“curvilinear 全面支持”。实现宜共享同一 CF 坐标解析器；剖面/Hovmöller 则定义从二维地理场抽取经纬线/带平均的操作规则。

## 4. 明确不会支持或暂不纳入当前实现的场景

- **UGRID 非结构网格**：现有 renderer 的栅格接口面向二维矩形数组，不消费 connectivity；仅依赖 xarray 打开文件不足以正确绘制，需要拓扑解析与多边形/线单元几何层，故应视为单独功能，不可宣称当前支持。
- **多面体与 cubed-sphere**：都需要格式专用的面/单元连接或 tile 拓扑重建，不能由普通 curvilinear 2D pcolormesh 自动覆盖。
- **完整 Panoply 投影集合**：当前只能选择 PlateCarree、Robinson、Mollweide、North/SouthPolarStereo、LambertConformal、Mercator 等显示投影（`render.py:17-32`）；显示地图投影选项不等于读取数据自身 CF `grid_mapping`。14 类投影数据的参数解析与源 CRS 转换仍不支持。

## 5. 我实际读了哪些文件

### NCViewer

- `core/dataset.py`（尤其 79-167 行）
- `plots/render.py`（尤其 17-67、285-406、416-525 行）
- `ui/plot_window.py`（尤其 56-86、355-379 行）

### Panoply 反编译源码

- `data/nc/NcVarTypeDetector.java`（尤其 46-88、130-174、484-595 行）
- `data/nc/NcArrayFactory.java`（尤其 57-132、149-271 行）
- `data/nc/array/NcArrayLonLatAuxiliary2D.java`
- `data/nc/array/NcArrayLonLatAuxiliary3D.java`
- `data/nc/array/NcArrayLonLatCartesian.java`
- `data/nc/array/NcArrayLonLatCubedSphereGMAO.java`
- `data/nc/array/NcArrayLonLatCubedSphereCAMSE.java`
- `data/nc/array/NcArrayLonLatPolyhedron.java`
- `data/nc/array/NcArrayLonLatProjected.java`
- `data/nc/array/NcArrayLonLatReducedCF.java`
- `data/nc/array/NcArrayLonLatReduced2D.java`
- `data/nc/array/NcArrayLonLatReducedISCCP.java`
- `data/nc/array/NcArrayLonLatUgridFaces.java`
- `data/nc/array/NcArrayLonLatUgridEdges.java`
- `data/nc/array/projected/` 中 14 个投影处理类及 `NcProjectionNames.java`（按 `NcArrayFactory` 分派表、检测器映射名称核对）
- `data/nc/gridder/NcGridderLonLat.java` 与 `NcGridderLonLatAuxiliary.java`、`NcGridderLonLatProjected.java`、`NcGridderLonLatCubedSphereGMAO.java`、`NcGridderLonLatCubedSphereCAMSE.java`、`NcGridderLonLatPolyhedron.java`、`NcGridderLonLatReducedCF.java`、`NcGridderLonLatReduced2D.java`、`NcGridderLonLatUgrid.java`、`NcGridderLonLatRotatedPole.java`
- `panoply/util/PanPlotType.java`
- `panoply/data/PanDataLonLatGridded.java`、`PanDataGeneral2D.java`、`PanDataTimeY.java`

> 行号均针对本次读取的工作区源码。Panoply 为反编译版本，结论基于其可见检测/分派实现。
