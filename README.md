# NCViewer — NetCDF 数据查看与绘图工具

一个中文界面的 NetCDF 数据查看 / 绘图桌面工具。不需要写代码，双击打开数据文件，就能看元数据、画地图 / 等值线 / 折线 / 剖面 / 矢量图。

适用于大四毕业论文、科研数据初步探索：打开 `.nc` 文件 → 看变量结构 → 画图 → 导出 PNG。

---

## 🚀 快速开始（小白版，不需要懂代码）

> 只需要三件事：**下载 → 解压 → 双击打开**。

### 1. 下载
从本仓库的 [Releases](../../releases) 页面下载最新版的 `NCViewer-windows-x64.zip`。

### 2. 解压
用右键"全部解压"，解压到一个文件夹（比如 `D:\NCViewer`）。

### 3. 运行
进入解压后的文件夹，**双击 `NCViewer.exe`**，程序就打开了。

---

## 📖 使用说明

### 第一次打开
1. 启动后会看到主窗口：左侧是数据浏览器，右侧是信息面板
2. 点左上角 **「打开」**（或按 `Ctrl+O`），选择一个 `.nc` / `.nc4` 文件
   - 也可以直接把 `.nc` 文件**拖进窗口**
   - 想先试试？用自带的示例数据 `data\demo_air.nc`（全球月平均气温）

### 看数据和画图
| 操作 | 效果 |
|---|---|
| 左侧树点开数据 → 点变量 | 右侧显示变量信息（维度、单位、范围等） |
| **双击变量** | 打开绘图窗口，自动画地图 / 折线 |
| 底部时间条 | 拖动滑块 / 点 ◀ ▶ / 输入序号，切换不同时次 |
| 右侧「绘图设置」 | 改投影、配色、等值线、标题等，即时生效 |
| `Ctrl` 选中多个变量 → 「合并绘图」 | 多个图拼在一起；选中 `u` 和 `v` 画矢量箭头图 |
| 绘图窗口 → 文件 → 导出图像 | 保存 PNG 图片，可直接放进论文 |

### 常用小技巧
- 极区数据（如北极海冰）**自动切换极地投影**，不用手动调
- 旋转 / 平移地图：绘图窗口工具栏的放大镜和手型按钮
- 数据只要经纬度（不用安装任何东西）：海岸线数据已内置，**无需联网下载**

---

## ✅ 环境要求

- Windows 10 / 11（64 位）
- 无需安装 Python，无需安装任何依赖

---

## ❓ 常见问题（FAQ）

**Q: 双击 exe 没反应 / 被杀毒软件拦截？**
A: 首次运行 Windows 可能提示"未知发布者"，点「更多信息」→「仍要运行」。如果杀软误报，把它加入白名单即可（这是未签名程序的正常现象，程序本身安全）。

**Q: 打开文件后显示"无法识别经纬度维度"？**
A: 说明这个数据的坐标维不叫 lat/lon。NCViewer 支持常见的经纬度命名和 CF 标准，但极特殊的网格（如某些非结构网格）暂不支持。

**Q: 能打开 GRIB / HDF 文件吗？**
A: 目前只支持 NetCDF（`.nc` / `.nc4`）。GRIB 请先用工具转成 NetCDF。

**Q: 画出来的图能直接放进论文吗？**
A: 可以。导出的 PNG 分辨率足够论文使用；如需更高精度，在绘图窗口调整后再导出。

---

## 🔧 开发者版（从源码运行）

想改代码 / 二次开发的同学看这里。

### 环境
- Python 3.11
- 依赖：`PySide6` `xarray` `netCDF4` `matplotlib` `cartopy` `cftime` `numpy` `pandas`

一键建环境（conda）：
```bash
conda create -n ncviewer python=3.11 -y
conda activate ncviewer
pip install PySide6 xarray netCDF4 matplotlib cartopy cftime numpy pandas
```

### 运行
```bash
cd ncviewer
python app.py            # 启动
python app.py 数据文件.nc # 启动并打开文件
```

### 测试
```bash
# 在项目根目录，用 ncviewer 环境的 python 依次运行：
python tests/test_ui_smoke.py
python tests/test_pipeline.py
# ... 共 11 个测试文件，全部通过为正常
```

### 项目结构
```
ncviewer/
├── app.py               # 入口
├── core/                # 数据层：打开 NetCDF、识别坐标/时间/辅助坐标
├── plots/               # 渲染层：地图/等值线/折线/Hovmöller/矢量，纯函数
├── ui/                  # 界面层：主窗口、数据树、绘图窗口、样式、图标
├── data/                # 示例数据 + 内置海岸线（离线可用）
└── tests/               # 测试（11 个文件）
```

---

## 🗺️ 支持的坐标系统

- 常规 1D 经纬度网格（lat/lon）
- 2D 辅助经纬度坐标（curvilinear grid，如旋转极网格 / 模式输出）
- CF 投影坐标网格（grid_mapping，如 WRF / NSIDC 海冰 EASE-Grid）
- 自动识别极区数据并切换极地投影

## 📄 许可证

本项目基于 MIT 许可证开源。海岸线数据来自 [Natural Earth](https://www.naturalearthdata.com/)（公有领域）。
