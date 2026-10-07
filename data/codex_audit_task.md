# Codex 审阅任务书：NCViewer 对非常规 NetCDF 数据的支持差距审计

## 任务背景
NCViewer 是一个 PySide6 + xarray + matplotlib/cartopy 的 NetCDF 查看绘图桌面工具（中文 UI）。
最近给它加了 curvilinear grid（2D 辅助经纬度坐标）支持。现在需要你（codex）作为独立审阅者，
对比**反编译的 Panoply Java 源码**与 **NCViewer 当前 Python 实现**，找出：
**Panoply 能处理、但 NCViewer 处理不了的非常规/特殊网格数据情况**，输出差距报告。

这是纯分析/审阅任务：**禁止修改任何代码**，只读源码 + 写报告文件。

## 必读环境卡
先读 `D:\Agent\deepseek\CODEX_ENV_CARD.md`（环境事实：Python 绝对路径、UTF-8、风格）。

## 材料位置

### A. Panoply 反编译源码（权威蓝本，只读）
根目录：`D:\Agent\deepseek\ncviewer\data\panoply_src\gov\nasa\giss\`

重点看（按优先级）：
1. **类型检测链**：`data\nc\NcVarTypeDetector.java`
   - `getVarType` → 离散类型 / gridded 类型 / projected lonlat / alternative lonlat 的完整判断顺序
   - `getAlternativeLonLatType`（UGRID → 多面体 → 立方球 → AUXILIARY_2D/3D → 旋转极 → 降分辨率）
   - `getGriddedVarTypeCS` / `getGriddedVarTypeNoCS`
2. **数组工厂**：`data\nc\NcArrayFactory.java`（createGeoCC / createGeneralXY / create1D 及各分支）
3. **特殊网格数组类**：`data\nc\array\` 下的：
   - `NcArrayLonLatAuxiliary2D.java` / `NcArrayLonLatAuxiliary3D.java`（2D/3D 辅助坐标——NCViewer 已支持 2D）
   - `NcArrayLonLatCartesian.java`（常规 1D 经纬度——NCViewer 已支持）
   - `NcArrayLonLatCubedSphereCAMSE.java` / `NcArrayLonLatCubedSphereGMAO.java`（立方球）
   - `NcArrayLonLatPolyhedron.java`（多面体球）
   - `NcArrayLonLatProjected.java`（投影网格，对应 crs/grid_mapping 变量）
   - `NcArrayLonLatReduced*.java`（Reduced2D / ReducedCF / ReducedISCCP 降分辨率）
   - `NcArrayLonLatUgrid*.java`（UGRID 非结构网格 Faces/Edges）
   - `projected\` 子目录 14 个投影类（AlbersEqualAreaConic/AzimuthalEqualArea/AzimuthalEquidistant/
     CylindricalEqualArea/Geostationary/GoesImager/LambertConformalConic/Mercator/MSGNavigation/
     RotatedPole/Sinusoidal/Stereographic/TransverseMercator/UTM + NcProjectionNames.java）
   - 每个类的 `canGridVariable` 判定条件 + `createAxes` 逻辑
4. **网格化器**：`data\nc\gridder\` 下 NcGridderLonLat*.java（看每种网格怎么转经纬度空间画图）
5. **绘图类型**：`panoply\util\PanPlotType.java`（12 种 plot type）+ `panoply\data\PanData*.java`
   （PanDataLonLatGridded / PanDataGeneral2D / PanDataTimeY 等）

### B. NCViewer 当前实现（只读，评估能力边界）
项目根：`D:\Agent\deepseek\ncviewer\`
1. `core\dataset.py`：
   - `find_aux_lonlat(ds, var)` / `_validate_aux_lonlat` / `get_aux_lonlat_arrays`（2D 辅助坐标识别）
2. `plots\render.py`：
   - `_aux_lon_lat(data)`（2D 辅助坐标检测，坐标维度是数据维子集即可）
   - `render_map` + `_render_map_aux`（pcolormesh 弯曲网格）
   - `render_vector`（含辅助坐标定位）、`render_line`、`render_contour`、`render_hovmoller`
   - `_vector_pair`（u/v 分量对识别）
3. `ui\plot_window.py`：
   - `_auto_polar_projection`（极区自动切极射）、`_apply_plot_type`（map/line/contour/hovmoller 判定）

## 任务输出（唯一交付物）
写报告到：`D:\Agent\deepseek\ncviewer\data\PANOPLY_GAP_AUDIT.md`

报告结构（中文）：
1. **结论摘要**：差距总数、哪些值得补、哪些不值得
2. **差距清单表**：每行一个数据类型场景，列：
   | 数据场景 | Panoply 检测条件（源码位置+简述） | Panoply 怎么画 | NCViewer 现状（支持/不支持/部分） | 差距严重度(高/中/低) | 实现建议(可选) |
3. **每个差距的详细说明**（对严重度=高/中的）：
   - 典型数据来源（什么工具/模式会产出这种数据，如 WRF/COSMO/卫星）
   - NCViewer 目前会怎样表现（报错？画错？还是画成普通图）
   - 用 xarray+cartopy 实现的大致思路（不用写代码，写思路）
4. **明确不会支持的场景**（如 UGRID 非结构网格），说明原因

## 审阅铁律
1. **只读分析，禁止修改/创建 ncviewer\ 下任何 .py 文件**（报告文件除外）
2. 每个结论必须**引源码依据**（文件+行号或类名+方法名），不许凭空判断
3. 独立判断，不要因为我写了"已支持 2D"就跳过验证——请实际读 NCViewer 代码确认
4. 若发现 NCViewer 声称支持但有 bug/边界情况，也列入报告（标注"边界缺陷"）
5. 报告写完后，在最后加一节"我实际读了哪些文件"清单（证明是真实审阅）

## 完成标志
报告文件已写入且结构完整。返回时只报告：报告路径 + 差距总数 + 严重度=高 的数量。
