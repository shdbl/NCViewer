# Panoply UI 布局规格（反编译提取，供 PySide6 重建）

来源：反编译 `D:\Panoply\PanoplyWin\jars\Panoply.jar`（PanoplyWin 5.x, 2024-12）→ `D:\Agent\deepseek\ncviewer\data\panoply_src\`（CFR 0.152，1102 个 java 文件，核心类在 `gov.nasa.giss.panoply.*`）。

## 一、主窗口 PanSourcesFrame（= sources/PanSourcesFrame.java + PanSourcesToolBar.java + PanDnVPanel.java + PanSourcesPanel.java）

- **整体布局**：垂直 BoxLayout = 工具栏 + 标签页(Datasets/Catalogs/Bookmarks) + 状态栏。窗口标题 "Panoply: Sources"（Windows 加前缀），可调大小，位置/大小记入 prefs。
- **工具栏顺序**（图标 36x36 + 可选文字）：创建绘图 | 合并绘图 | 打开数据集 | (glue) | 移除一个 | 移除全部 | (glue) | 隐藏信息。按钮在无数据集时禁用。
- **Datasets 面板（PanDnVPanel）**：左右分割（BlackSplitPane），左=树表格 + 底部 "Show:" 变量类过滤器下拉（所有变量/可绘图变量），右=等宽字体 CDL 元数据信息面板。信息面板宽度 15%-85% 可调，记 prefs。
- **树表格（NcDataTreeTableModel）**：三列 `Name | Long Name | Type`（对齐 {左,左,右}）。数据集行=文件名(+Local File)；变量行=短名|长名|类型(如 Geo2D/1D)。双击变量→创建绘图；右键→弹出菜单；支持拖放、搜索 Find。
- **右侧信息面板**：JEditorPane `text/plain` Monospaced 12pt 不可编辑，选中节点变化才刷新（oldNode_ 缓存），显示 `getDetail(enhanced)`=CDL 语法文本。
- 双击(selectionMade id==102) 且节点是 NcVariable → create-plot。

## 二、绘图窗口 PanPlotFrame（= plotui/PanPlotFrame.java + PanPlotTabbedPane.java）

- **标题**：`{变量短名} in {数据集名}`，vname≤28 字符、dname≤42 字符，重名追加序号。
- **布局**：垂直 = PanPlotTabbedPane（标签页）+ 状态栏。标签页 tab0="Plot"(PanPlotScrollPane 滚动+图居中)，tab1/2=Array 1/Array 2（PanArrayDataPanel 数据表格）。标签可拖动排序、可切换（菜单 show-plot/show-array-1/show-array-2）。
- **控制面板（createControls）**：按 plot type 生成多个 PanControlsPanel，存 Hashtable<PanPlotControlsID,PanControlsPanel>：
  - 全部：ARRAYS(数组切片)、LAYOUT(布局)、LABELS(标签)
  - 地图(lonlatMap)：MAP(投影)、GRID(经纬网格)、OVERLAYS、SHADING、SCALE
  - 色等值线(colorContour)：GRID、CONTOURS(等值线)、SCALE
  - 折线(line)：GRID、STROKE、SCALE
  - 呈现方式：浮动 windoid 或伪调色板（本项目简化为右侧 QDockWidget 停靠）。
- **尺寸**：最小 540x570；MAX_VIS_PLOTS=8；图在 overHolder 中居中（pleft/ptop=(phsize-psize)/2）。

## 三、时间/维度切片 PanArraySlicer（关键——用户要的 Panoply 式时间选择）

- 布局（水平一行，PanArraySlicer.java + PanArraySlicePanel.java）：
  `{维长名}:` + **spinner(1..length)** + ` of {length} = ` + **comboBox(格式化值，如 2015-01-01)** + 单位label + [Avg checkbox] + 链接bullet(•)。
- **spinner ↔ combo 双向联动**（spinner 变化 setSelectedIndex、combo 变化 setValue）。combo 列出维度全部值（NcDimensionListModel，格式化日期）。
- 无自由维度时显示 "No additional dimensions."；PanArraySlicePanel 标题 `Array {n}: {shortname}`。
- 每帧可多个 slicer（各自由维度一个），改变即 `setDataSlice(vnum, dimIndex, index)`。

## 四、数据表格 PanArrayDataPanel（View Data 视图）

- **顶部**：Dataset: / Variable: / Units: / Slice: 标签（FlexingGridLayout 2列）。
- **中部**：JTable 数据 + TableRowHeader 行头 + X Axis/Y Axis 轴标签（含长名+单位）。
- **底部**：`Data Format:` 下拉(%.7G) — Flip table B/T — Flip L/R — Show cell indices — `Row/Col Header Format:` 下拉。
- 1D 数据垂直表格；2D 矩阵表格。

## 五、CDL 元数据（右侧 infoPane / View Metadata）

- netcdf 语法：`netcdf file { ... }`，含 dimensions / variables(每行 `dtype name(dims);` + attrs) / global attributes。等宽字体。

## 六、控制面板通用结构（PanContourControls / PanLabelControls / PanLonLatMapControls）

- 每个面板：垂直 BoxLayout；每行 = `标签: 控件`（QuickBox.createLeftBox），行间 1px 竖直 strut；标签宽度 matchLabelWidths 对齐。
- **Contour**：Locations: / Style: / Color:+Weight: % / Labels: Visible+Size:。
- **Label**：Title: / Subtitle: / Footnotes Left/Center/Right + Show data min-max / Typeface: / Sizes: Title-Subtitle-Footnotes / Exponents(超10)。
- **Map**：Projection: 下拉 / Center on: Lon. °E, Lat. °N / 投影参数行 / 灰色小字提示 "Use 'Grid' controls to manage drawing of parallels and meridians."

## 七、PySide6 重建映射（本项目实际采用）

- 主窗口工具栏：QToolBar 图标按钮（打开数据集/创建绘图/移除/隐藏信息）——保留已有 open_icon/refresh_icon + 新增 plot 图标。
- 树：QTreeWidget 三列（名称/长名称/类型），两级（数据集→变量），保留 item_payload + Qt.UserRole，双击→new_plot。
- 元数据：右侧 QTabWidget「概览/原始信息」，原始信息=CDL 等宽文本（复用 cdl_text）。
- 绘图窗口：QTabWidget「可视化/查看数据/查看元数据」三视图 + 顶部 Panoply 式时间选择器（time_spin + " of N = " + time_combo 日期）+ 滑块 + 底部状态栏；右侧 QDockWidget 绘图设置。
- 时间选择器保留测试契约：time_spin.setValue(5)→slider.value()==4；time_label 显示真实日期字符串。
