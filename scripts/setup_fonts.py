"""配置 NCViewer 使用的中文字体。"""
import matplotlib
matplotlib.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Noto Sans CJK SC"]
matplotlib.rcParams["axes.unicode_minus"] = False