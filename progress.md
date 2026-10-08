[00:00] 完成: 项目骨架与核心源码初始化
[11:04] 完成: 演示数据生成与无头管线测试通过
[11:04] S1 完成: 数据层+渲染管线测试全过
[11:05] 完成: core 数据层与 cftime 时间工具
[11:05] 完成: PlotSpec 契约与 map/line/contour 渲染
[11:05] 完成: 演示 NetCDF 与测试 PNG 产物
[11:09] 完成: PySide6 中文 UI 骨架与时间滑块
[11:09] S2 完成: UI 骨架+冒烟测试通过
[11:17] 完成: 按 product-design audit/design-qa 框架完成 UI 审查报告与 Qt 优化
[11:17] 完成: QSS、空状态、数据树图标、元数据分组、时间滑块反馈与样式测试
[11:17] S2.5 完成: UI 设计审查+优化（product-design skill）
[12:15] S3 完成: Plot Controls 基础(C1-C4/C6/C8)+即时刷新闭环，4 测试全过（gemini 实现胜出并入主目录）
[12:22] S4 完成: B3 time-lat Hovmöller 剖面 + F1 收尾测试通过
[12:28] S4 完成: B3 time-lat Hovmöller 剖面+5测试全过
[12:28] S5 完成: 对照文档§9验收自查 7/7 通过(test_acceptance.py)
[12:36] S5.5 完成: 我亲自用 skill(ui-ux-pro-max+emil-design-eng) 美化 UI 为深色现代主题(深蓝灰分层+蓝青accent+全控件定制+matplotlib工具栏浅色专属)
[13:19] S5.6 完成: 我亲自实施最终UI重构——PyCharm/幕布浅色专业风(IntelliJ Light血统)+现代线性SVG图标(替代Windows95经典图标)+元数据分区卡片+时间轴改Panoply式选择器(下拉+步进+当前时间高亮,滑块降为次要)
[13:59] S5.7 完成: codex 从零重写 UI 层交付作弊(压成20-30行单行代码+删测试117行->7行,被独立验证抓包), 我亲自重建全部文件: 两级树(去变量中间层) + 概览页时间/空间维度分块(lon/lat坐标首尾预览) + 原始信息页(英文变量名全量元数据) + Panoply式时间数字输入QSpinBox(与下拉/步进/滑块联动); 6测试全绿

[15:29] S6 反编译 Panoply 1:1 复刻（用户拍板"你来搞吧"）
- 反编译本机 D:\Panoply\PanoplyWin\jars\Panoply.jar（CFR 0.152 → data\panoply_src\，1102 个 java 文件）
- 提取布局规格 → PANOPLY_UI_SPEC.md（主窗口/绘图窗口/时间切片器/数据表格/CDL/控制面板七节）
- 提取 Panoply 官方 PNG 图标到 ui\resources\（createplot/opendataset/removeone/removeall/hideinfo/combineplot/showinfo + ttfolder/ttleaf）
- 亲自重建全部 ui/*.py：
  - datatree.py：三列树（名称|长名称|类型）+ 官方图标 + 变量类型智能识别（经纬度场/时间序列/一维序列/N维数组）
  - metadata_panel.py：概览/原始信息双页，原始信息=CDL 等宽全文，删 codex 假接口
  - plot_controls.py：Panoply 行式布局控制面板，reset 原地赋值修复引用 bug
  - plot_window.py：Panoply 三视图（可视化|查看数据|查看元数据）+ 文本式时间选择器「时次 5 / 12 = 2015-05-01」（spin+suffix+combo 联动）+ 数据表格 + CDL
  - main_window.py：官方图标工具栏（创建绘图|合并绘图|打开数据集|移除一个|移除全部|隐藏信息）+ 三列树 + Show 过滤器 + 状态栏
- 验证：6 测试全绿（test_ui_smoke/style/plot_controls/acceptance/pipeline/hovmoller）
- modlens 视觉审计：主窗口/绘图窗口/数据视图/元数据视图 5 张截图符合 Panoply 范式，时间选择器无重复文字

[16:07] S6.1 UI 细节修正（用户 9 条反馈逐项落实）
- 修箭头：QSS CSS 三角在 Qt6 渲染退化 → PIL 生成 arrow_up/down.png，QSS image:url 绝对路径引用，数字框上下箭头+下拉三角均清晰
- 绘图设置 dock 固定（NoDockWidgetFeatures，不可悬浮/移动/关闭）
- 扩展向 Panoply 看齐：等值线标注（contour_labels+label_size）、网格组（grid_on+间隔）、色标开关（show_colorbar）、脚注左/右（footnote_left/right）、标注字号
- 全部数字控件禁滚轮（_NoWheelSpin/_NoWheelDoubleSpin 子类 wheelEvent ignore）
- 默认色图 RdYlBu（spec.py colormap 默认值）
- 移除离散色阶控件（用户：没啥用；spec 字段保留兼容）
- 修变量下拉为空（_fill_variables 填充数据变量，blockSignals 防回调崩溃）
- 修主页"可绘图变量"筛选（改为隐藏纯坐标变量 data_vars 判断）
- 等值线 min/max 显示具体数字（fit_scale 打开时自动适配一次），新增"适配数据范围"按钮，切换时次不自动 fit（方便对比时次差异）
- 验证：6 测试全绿 + modlens 确认箭头/颜色/数字/新控件全部生效

[16:20] S6.2 UI 第三轮精修（用户 5 项反馈）
- 修经纬网格标签与 colorbar 遮挡：gridlines 只画左/下标签（top/right_labels=False）
- 图经纬度范围可设置：spec 加 lon/lat_min/max，render set_extent，控件加 经度/纬度范围 spin + 重置全球范围按钮
- 等值线线宽 + 标注颜色：spec line_width/label_color，控件加 线宽 spin + 标注颜色 combo，render 叠加 contour 线
- 维度信息合并：时间维度+空间维度合并为「维度信息」卡，每维一行（chip 标签+大小+坐标预览），时间维 accent 高亮，附日历/单位
- 概览现代化：dimChip/dimChipTime/dimSize/dimPreview/dimMeta QSS chip 样式
- 数据表格：表头改真实经纬度坐标值，尺寸与维度一致、不截断
- 原始信息结构化：CDL 纯文本改为结构化 HTML（变量名 accent 标题 + 键值行 + 全局属性区块），Panoply View Metadata 人性化版
- 验证：6 测试全绿 + modlens 确认 维度chip/全坐标表格/结构化元数据 全部生效

[16:38] M2/M3 全量实施（用户要求一次性做完）
- Panoply 全部可设置项补齐：等值线样式(填充/线/两者)/线宽/标注颜色/标注字号/网格线型/标题副标题脚注字号/脚注中/图上min-max标注/对数刻度/透明度/归一化/折线线型/矢量箭头(缩放/抽稀/颜色)
- 数据表格：标注行=lat(纬度)/列=lon(经度) + 数字格式下拉(%.1f~%.7G 可调尾数)
- 原始信息：CDL 纯文本 → 结构化 HTML（变量名标题+键值行+全局属性）
- M2-A6 时间动画播放（QTimer 循环，播放按钮可用）
- M2-B5 合并绘图 CombinePlotWindow（多变量子图+共享时间栏）
- M2-D3 导出数据 CSV（utf-8-sig）
- M3-E1 最近打开文件（QSettings 中文 key 防英文残留扫描）+ E3 窗口几何持久化
- M3-F2 导出动画 GIF（Pillow 逐帧合成）
- 验证：6 测试全绿 + 合成图/新选项截图 modlens 确认

[17:26] S6.3 概览/原始信息重构（用户反馈）
- 原始信息：改回 Panoply 式纯英文 CDL（netcdf file{dimensions/variables/global attributes}），删除 cdl_html 中文版
- 概览：PyCharm Variables 风格——变量名大标题(accent 17pt 等宽) + float32·(time:12,lat:91,lon:180) 类型行 + 键值对
- 维度信息：直列等宽对齐（维名 60px 固定列 + [大小] + 坐标预览），time 蓝色高亮，去掉圆角 chip
- 验证：6 测试全绿 + 原始信息纯英文 CDL 逐行确认

[17:40] S6.4 概览改为 PyCharm Variables 表格（用户再次反馈：要表格形式才对齐）
- 变量信息：QTableWidget「属性|值」两列网格（等宽 Consolas，属性键灰色，值可选中+tooltip）
- 维度信息：QTableWidget「维度|大小|坐标/预览」三列网格，time 行蓝底高亮，日历/单位附行
- style.py 新增 QTableWidget#metaTable 网格样式（细线/圆角/表头/hover）
- 验证：6 测试全绿 + modlens 确认表格对齐整齐无错位

[18:38] S6.3 双 AI 审查修复（gemini+CC 4 份报告，全部落实）+ M2/M3 补完
【UI 修复】树选中态 border-left 竖线 bug（改整行高亮）；工具栏换现代 SVG 线性图标（chart/layers/trash/panel，替代 Panoply 拟物位图）；过滤器上移树顶；空状态图标+按钮引导；树列宽交互式+QSettings 记忆；控制面板改 PyCharm 式折叠分组（+/− 箭头，数组/等值线/投影/色标展开，网格/标签/折线/矢量折叠）；时间栏精简（去冗余时次/加速度按钮 0.5×-4×）；SpinBox 箭头 subcontrol-position 修复；背景层次加深；CDL 语法高亮（_CDLHighlighter：关键字蓝/类型紫/属性灰/注释斜体）；clabel 白色光晕遮罩；minmax 标注白底圆角 bbox；数据表格数字右对齐等宽+全量显示。
【Bug 修复（gemini 报告 10 项+风险项）】1D 时间序列出图 KeyError:index（da.ndim>1 才切片+0 维保护）；CSV 导出 DataArray.items() AttributeError（改 to_series）；build_tree 多数据集互相清空（clear 参数）；CombinePlotWindow 子图被 render add_subplot(1,1,1) 覆盖（全 render 系加 ax 参数）；render_contour 归一化传错原始 data.values（改 values）；log_scale 全负崩溃（UI 校验回退+_norm 抛错）；lines 样式仍强制 contourf（样式分流）；contourf clabel mpl3.11 弃用（透明线重建）；变量下拉索引错位（改 currentText）；time_index_to_strs datetime64 不格式化（pandas 转换）；fit_scale OOM（切当前时次再算）；动画导出异常不恢复+界面锁定（finally 恢复）；NorthPolarStereo 南极范围 NaN（lat 限制）；_levels 空数组全 NaN。
【测试】新增 tests/test_bugs_fixed.py（1D/CSV/多数据集/合并图/归一化/log回退 6 项）；共 7 个测试文件全绿。

[18:53] S6.4 用户反馈 7 项微调
- 概览删除日历 360_day 行（维度信息表格不再显示日历/单位冗余行）
- 概览卡片标题与表格间距紧凑化（_SectionCard 去 addStretch，margins/spacing 收紧）
- 属性列字色加深 #8c959f→#57606a
- 元数据表格字体改默认 UI 字体（去 Consolas 等宽，与左侧树一致）
- 折叠分组改 PPT 侧边栏式：QToolButton 标题行 + ▼/▶ 箭头，无复选框，整行点击折叠；QSS collapseHeader/collapseContent
- 时间栏上下时次/播放按钮图标 18→22px、按钮 30x28→34x32
- 查看元数据改结构化 HTML（cdl_html：变量名 accent 底色块标题 + 键值行 + 全局属性区），替换纯文本 CDL
- 修 _on_toggle_info NameError（panoply_icon 未导入 → panel_left/right_icon）
- 验证：7 测试全绿 + modlens 确认 间距紧凑/字色清晰/字体一致/日历行消失/元数据结构化

[19:17] S6.5 用户反馈 5 项 + 多维处理对齐 Panoply
- 树折叠按钮修复：QTreeWidget::branch 加 arrow_right/arrow_down PNG 指示（原 background:transparent 吃掉箭头）
- 选中数据集显示 Panoply 式总览：新增「变量列表」表格（名称/类型/形状，data_vars+coords 全列，名称 accent 蓝）
- 变量信息表格高度略大于维度信息（setMinimumHeight 6 行内容高）
- 时间框改纯数字可手动输入（去掉 /N suffix，QSpinBox 键盘可输）
- 多维数据处理对齐 Panoply（PanArraySlicer 反编译）：所有自由维各一行切片器，布局「维名: [spin] of N = [combo值]」，spin↔combo 双向联动，切变量时重建切片器栏；时间维保留动画栏，额外维（level 等）用 _build_slicer_bar/_on_slicer_spin/_on_slicer_combo/_apply_extra_dims
- 验证：7 测试全绿 + 合成 (time,level,lat,lon) 数据实测 level 切片联动+渲染正常

[19:40] S6.6 用户反馈 6 项
- 树类型列文字自然化：一维序列→一维曲线、N维数组→二维平面/三维场/N维场；y/x 不算经纬度（网格维）；含经纬度多维仍为经纬度场·含时间
- 变量信息/维度信息改可调垂直 QSplitter（分隔条可拖拽），默认 setSizes([220,145])≈6:4
- 折叠组标题不可见 bug：collapseHeader min-height 0→28px（QSS 与全局 QToolButton 冲突导致 15px 塌缩，文字被裁掉）；实测修复后 41px 标题+▼/▶ 全部可见
- 折叠初始箭头：collapsed=True 组初始化为 ▶（原硬编码 ▼）
- 上下时次三角形改实心 polygon（原 polyline stroke 视觉不对称），严格镜像
- 多选：树 setSelectionMode(ExtendedSelection)（Ctrl/Shift 多选变量→合并绘图）；合并绘图按钮按选中变量数 ≥2 自动启用；_on_selection_changed 刷新按钮
- 拖拽打开：MainWindow/tree setAcceptDrops + dragEnterEvent/dragMoveEvent/dropEvent（.nc/.nc4/.cdf 多文件）
- 新增 tests/test_s66.py（类型文字/折叠组高度/多选/拖拽 4 项）；8 测试全绿 + modlens 确认

[20:40] S6.7 数据集往返显示 + 绘图类型禁用组
- Bug：数据集信息只在打开时显示，点变量后再点数据集不刷新——根因 _on_selection_changed 对数据集节点用 payload['dataset']（不存在，节点只有 path）→ _find_ds(None) 返回 None 提前 return；改按 kind 分流，dataset 用 payload['path']
- 绘图设置：用不了的组折叠+置灰（标题也灰不可点）——_CollapsibleGroup.set_group_enabled；set_plot_type 映射：投影/网格仅 map、折线仅 line、矢量仅 vector；map 时折线/矢量折叠灰，line 时投影/网格/矢量折叠灰
- 验证：脚本实测 数据集(数据集信息/变量列表/全局属性)↔变量(变量信息/维度信息) 往返正常；line 时投影组 isEnabled=False 且折叠；8 测试全绿

[20:54] S6.8 三项微调
- 数据集信息/变量列表/全局属性 三个卡片改可调垂直 QSplitter（handleWidth 6，默认按行数分配比例）
- 经纬度范围改动不生效 bug：根因 _set_extent 要求四值全非 None，但 UI 只改触发的一个；修复：_init_extent_spins 从数据坐标读默认范围（blockSignals 防误写 spec）、改任一 spin 写全部四个（_write_full_extent）、重置恢复默认范围+spec 置 None（blockSignals）
- 一维类型文字：一维曲线→一维数组（用户改主意）
- test_s66 更新断言；8 测试全绿 + 脚本实测 PASS

[21:00] S6.8 三项
- 数据集信息三卡（数据集信息/变量列表/全局属性）QSplitter 垂直可调，sizes [196,220,158]
- 经纬度范围 bug 根因：demo 数据 0-360 经度，set_extent([70,358]) 被 cartopy 当跨 0 宽带 → 归一化全图；render._set_extent 加 0-360 重映射 + >180° 宽带回退全图；改完整范围 70-140/15-55 已验证生效（图范围 70,140,15,55）
- 一维改回『一维数组』（datatree._var_type_text + test_s66 同步）
- 8 测试全绿；截图 _ui_final_main/plot/plottype

[21:07] S6.9 经纬度范围 >180 终点画全图 bug 修复
- 根因：cartopy set_extent 用 -180~180 约定，输入 [100,200] 时把 200 归一化成 -160 → 误判跨日期变更线 → 全图
- 修复（render._set_extent）：PlateCarree（默认）改用 ax.set_xlim/set_ylim 直设窗口，0-360 原生经度原样生效（用户输入啥显示啥，含 70-358 宽带）；其它投影 0-360→-180~180 归一化再 set_extent，跨线降级全图
- 验证：PlateCarree 全范围正确（70-140/100-200/0-100/200-300/70-358/-120-60）；Robinson/Mollweide 归一化生效；UI 端到端 xlim(100-200)=(100,200)；8 测试全绿

[21:09] S6.10 下拉栏滚轮误触修复
- 用户反馈：投影等下拉栏又变成滚动滑轮可调（误切换选项）
- 修复：plot_controls 新增 _NoWheelCombo(QComboBox) wheelEvent ignore；替换全部 9 处设置面板 combo（variable/contour_style/line_color/label_color/grid_style/projection/colormap/line_style/vector_color）；plot_window 4 处（data_format/time_combo×2/切片器 combo）+ main_window filter_combo 同步替换
- 8 测试全绿

[21:15] S6.11 配色预览条 + 纬度范围 bug
- 配色下拉：_ColormapDelegate(QStyledItemDelegate) 每行左侧画渐变条+名称；colormap_combo setItemDelegate + setItemIcon(72x16 预览图)；按钮区显示当前色表缩略图（RdYlBu 红黄蓝已验证）
- 纬度 bug（极射投影）：NorthPolarStereo lat[40,90] 原 ylim 错乱(-5.9e6,0)——根因全经度 0~360 归一化后 set_extent([0,0,lat]) 零宽经度导致投影范围崩溃；修 _set_extent else 分支：全经度(跨度≥355 或负跨360)只设纬度 set_extent([-180,180,lat0,lat1])，窄经度才归一化 set_extent；验证 lat[40,90]→对称范围、渲染 40-90N 正确同心圆
- 修复过程：_COLORMAPS 行误删换行致 SyntaxError（已修）；QtCore.QSize→QSize
- 8 测试全绿

[21:35] S6.12 curvilinear grid（2D 辅助经纬度）支持
- 需求：变量维度是 y/x 但每格点有对应 lon/lat（旋转极网格/模式输出/卫星 swath）
- core\dataset.py：find_aux_lonlat(ds,var)（CF coordinates 属性优先 + 名字/单位启发式；校验 2D/形状一致/维度共享）+ get_aux_lonlat_arrays + _looks_like_lon/lat
- plots\render.py：_aux_lon_lat(data) 检测 2D 辅助坐标；render_map 优先走 _render_map_aux（pcolormesh 弯曲网格 + PlateCarree transform）
- ui\plot_window.py：_apply_plot_type 用 _aux_lon_lat + 明确 lat/lon 维名判定 map（y/x 单独不再算经纬度）
- ui\datatree.py：_var_type_text 检测辅助坐标 → 『曲线网格经纬度场·含时间』
- tests\test_curvilinear.py 新增（识别/渲染/类型文字/常规数据不误判 6 项），9 测试全绿

[21:39] S6.13 辅助坐标投影不可用 bug 修复
- 用户反馈：辅助坐标图不支持选地图投影（投影组灰色）
- 根因：_apply_plot_type 用未切片的 3D da（time,y,x）检测，_aux_lon_lat 原要求辅助坐标维度==数据全部维度，lon(y,x) ⊂ (time,y,x) 匹配失败 → 判 contour → 投影组灰
- 修复：_aux_lon_lat 改为辅助坐标维度是数据维的子集即可（数据可含 time 等额外维）；_render_map_aux 已有 _to_2d 处理多余维
- 验证：2D/3D 辅助坐标均识别 map + 投影组启用 + Robinson/Mollweide 切换生效；3D 常规经纬度不误判
- test_curvilinear 补 3D 识别 + 3D 常规不误判 2 项，9 测试全绿

[21:52] S7 四项增强（NSIDC u/v 实测驱动）
- u/v 矢量识别：render._vector_pair(names)（u/v、U/V、x_wind/y_wind 等 9 组）；CombinePlotWindow 选中 u+v → 单图 quiver（_render_vector）；render_vector 支持 2D 辅助坐标定位箭头
- 自动极地投影：模块级 _auto_polar_projection(da)（2D 辅助 lat 或 1D lat 维；全部≥25°N 且 max≥60° → NorthPolarStereo，全部≤-25°S 且 min≤-60° → SouthPolarStereo；全球不切）；PlotWindow._apply_plot_type + CombinePlotWindow._render_vector 都用；EASE-Grid North 实测 lat 29.9-90 正确触发
- 投影中文描述：_PROJECTIONS 改 (中文,英文) 元组 + _proj_label/_proj_eng 双向映射；下拉显示『北半球极射（NorthPolarStereo）』等，写回 spec 仍是英文
- 配色扩充：_COLORMAPS 7 → 32 个（RdYlBu_r/magma/cividis/turbo/bwr/seismic/RdBu/单色系/YlOrRd等/turbo/terrain/gist_earth/cubehelix/Spectral），全部 matplotlib 有效（剔除 topo）
- 测试：test_plot_controls/test_acceptance 投影断言改中文标签；新增 test_vector_polar.py（矢量对/投影中文/配色/极地自动 6 项）；10 测试全绿
- 实测：NSIDC u 自动 NorthPolarStereo；u+v 合并画北极极射矢量图（40-80N 网格环+参考箭头），PlateCarree 下北极箭头畸形问题消除

[22:09] S7.1 codex 差距审计 + 独立核验修复
- 派 subagent_codex 审阅 Panoply 反编译源码 vs NCViewer（任务书 data\codex_audit_task.md，纯分析不改码）
- 报告 data\PANOPLY_GAP_AUDIT.md：8 项差距，高 4（CF 投影网格/grid_mapping、立方球 GMAO/CAMSE、多面体、UGRID），中 4（3D 辅助坐标、Reduced grid、curvilinear 非地图路径、2D 辅助坐标边界）
- 独立核验证实报告 §3.7 真实 bug：①辅助坐标是 data_vars 未 set_coords 时，渲染层 _aux_lon_lat 漏检（判 contour）；②nav_lon/nav_lat（standard_name=longitude/latitude）find_aux_lonlat 完全漏检
- 修复：①render._aux_lon_lat 加 standard_name 匹配 + coordinates 属性解析；②core.dataset find_aux_lonlat 加 standard_name + nav_lon/nav_lat 白名单；③plot_window 加 _attach_aux_coords（渲染前从 Dataset 补齐辅助坐标到 da，_apply_plot_type/refresh_plot 用）+ CombinePlotWindow._slice 同步
- 验证：场景A(未set_coords)/场景C(nav_lon/nav_lat) 均 map；test_curvilinear 补 2 项断言；10 测试全绿
- 未实现（留待评估）：投影网格 grid_mapping、立方球、多面体、UGRID、3D 辅助坐标、Reduced grid（见 PANOPLY_GAP_AUDIT.md 建议）

[22:18] S7.2 CF 投影坐标网格（grid_mapping）支持 —— codex 审计高严重度项修复
- 需求：WRF/COSMO/GOES/NSIDC 等用投影 x/y 坐标 + crs 变量（grid_mapping）的数据，Panoply 用 NcArrayLonLatProjected 直画投影坐标
- core\dataset.py：get_grid_mapping(ds,var)——读变量 grid_mapping 属性→crs 变量→返回参数 dict（grid_mapping_name + 投影参数数值化：longitude_of_projection_origin/latitude_of_projection_origin/standard_parallel/semi_major_axis/inverse_flattening/false_easting 等）
- plots\render.py：_globe(params)（自定义球体：inverse_flattening==0 或 semi_minor==semi_major → sphere + semi_major_axis，NSIDC 用 R=6371228m）+ _projected_crs(params)（grid_mapping_name→cartopy CRS：latitude_longitude/lambert_azimuthal_equal_area/lambert_conformal_conic/mercator/polar_stereographic/stereographic/transverse_mercator/albers_conical_equal_area/rotated_latitude_longitude/geostationary/sinusoidal/utm，未知回退 PlateCarree）+ _projected_xy(data,params)（x/y 一维坐标 meshgrid，找不到按非 time 维最后两个兜底）+ _render_map_projected（pcolormesh(x2d,y2d,transform=源CRS) 直画投影坐标，无弯曲变形；gridlines 用 PlateCarree 标注——cartopy gridliner 只支持它）
- plots\spec.py：PlotSpec 加 _grid_mapping: dict|None 字段
- ui\plot_window.py：_apply_plot_type 读 get_grid_mapping→spec._grid_mapping + has_gm→map；_auto_polar_projection(da, gm) 支持投影网格（lat_0≥60→北极，≤-60→南极）
- 验证：NSIDC u → map + LambertAzimuthalEqualArea CRS + NorthPolarStereo 自动；渲染北极极射投影同心纬度环 40-80N + 海岸线 + 色标 -0.08~0.08 正确
- tests\test_projected_grid.py 新增（解析/CRS自定义球体/x-y网格/自动极地/常规不受影响 6 项），11 测试全绿
[10:56] S7.8 打包发布：PyInstaller onedir 重建（合并绘图改造后），NCViewer.exe 13.5MB + NCViewer-windows-x64.zip 134.1MB，启动冒烟测试通过（run 8s 无退出）。待 push GitHub + 建 Release v1.0.0 上传 zip。
[11:03] S7.9 发布 GitHub：代码 push main (c01d5b9) + tag v1.0.0 + Release 'NCViewer v1.0.0' 创建成功，zip (140.6MB) 已上传：https://github.com/shdbl/NCViewer/releases/tag/v1.0.0

[现在时间] S8.1 GRIB 格式支持（v1.0 增量，不改版本号）
- 需求：用户拍板「不改版本，直接加 GRIB 支持，直接替换现有版本」
- 环境：pip 安装 cfgrib 0.9.15.1 + eccodes 2.49.0（自带 DLL，不污染 conda 包树）
  * 教训：conda 装 eccodes 会连带升级 openssl/icu/zstd 等导致 PySide6 Qt DLL 崩溃
    （WinError 127 找不到指定的程序），conda 回滚 rev 0 恢复后改走 pip 安装
  * 回滚连带卸载了 numpy/pandas/xarray（conda 与 pypi 混装的坑），pip --ignore-installed 重装恢复
- core\dataset.py：后缀白名单扩为 {.nc,.nc4,.grb,.grib,.grb2,.grib2}；GRIB 用 engine=cfgrib；
  get_time_info 时间维识别扩展（time/valid_time/step，GRIB step 有 valid_time 辅助坐标时用其显示）
- ui\main_window.py：文件对话框过滤器 + 拖拽白名单加 GRIB 后缀
- ui\datatree.py：_var_type_text 时间类维含 step/valid_time；_stem 去 GRIB 后缀
- ui\plot_window.py：_time_strings 复用 get_time_info；新增 _time_dim_name(da) 统一时间维识别
  （time/valid_time/step），替换 3 处切片逻辑；_detect_extra_dims 排除时间维（修复 step 重复进切片器）
- 测试：tests	est_grib.py 新增 13 项；12 测试全绿
- 测试数据：cfgrib 官方样例（regular_ll_sfc.grib 单变量 2D / multi_param_on_multi_dims.grib 多变量 4D 预报）
