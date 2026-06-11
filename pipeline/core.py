# -*- coding: utf-8 -*-
"""基础层:主题配色、字体降级链、缓动函数、文本绘制原语。

由原 animate.py(基础工具)+ animate_fun_full.py(浅色主题覆盖)重构而来。
颜色一律通过语义名(BLUE/GOLD/GREEN/...)访问当前主题 `C`,storyboard 里
也用语义名引用,换主题不改内容。
"""
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib import font_manager

# ----------------------------------------------------------------------------- 字体降级链
# 原项目在 Windows 上用 YaHei/SimHei;按开发方案做探测降级,CI/macOS 也能出片。
CJK_CHAIN = [
    "Microsoft YaHei", "SimHei",                      # Windows
    "PingFang SC", "Hiragino Sans GB", "PingFang HK",  # macOS
    "Heiti TC", "STHeiti", "Arial Unicode MS",
    "Noto Sans CJK SC", "Source Han Sans SC",          # Linux / CI
    "Songti SC", "SimSun",
]


def setup_fonts():
    """探测可用 CJK 字体并写入 rcParams,返回实际命中的链。"""
    avail = {f.name for f in font_manager.fontManager.ttflist}
    chain = [c for c in CJK_CHAIN if c in avail]
    plt.rcParams["font.sans-serif"] = chain + ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["mathtext.fontset"] = "cm"
    return chain


FONT_CHAIN = setup_fonts()

# ----------------------------------------------------------------------------- 主题
class Theme:
    """语义配色。属性名 = storyboard 里可引用的颜色名。"""

    NAMES = ["BG", "WHITE", "MUTED", "GRID", "BLUE", "GOLD", "GREEN", "PINK",
             "RED", "HP", "HPTRACK", "GPANEL", "GSPINE"]

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

    def resolve(self, name, default=None):
        """'GOLD' -> '#c2780c';'#abc123' 原样返回。"""
        if name is None:
            return default if default is not None else self.WHITE
        if isinstance(name, str) and name.startswith("#"):
            return name
        return getattr(self, name)


THEMES = {
    # 深色 navy(原 animate.py 默认)
    "navy": dict(
        BG="#0f1226", WHITE="#f4f6ff", MUTED="#9aa3c8", GRID="#2a2f57",
        BLUE="#6cc6ff", GOLD="#ffcf6e", GREEN="#86efac", PINK="#ff95a8",
        RED="#ff5a6a", HP="#7CFC9B", HPTRACK="#0b0e22",
        GPANEL="#12173a", GSPINE="#3a4070",
    ),
    # 浅色"纸面"(原 animate_fun_full.py 覆盖,full2 成品所用主题)
    "paper": dict(
        BG="#f6f8fc", WHITE="#1f2a44", MUTED="#475569", GRID="#dbe3f0",
        BLUE="#2563eb", GOLD="#c2780c", GREEN="#0f8a3d", PINK="#ec5a86",
        RED="#e11d48", HP="#15a34a", HPTRACK="#eef2f8",
        GPANEL="#ffffff", GSPINE="#c4cfe0",
    ),
}

C = Theme(**THEMES["paper"])   # 当前主题(模块级单例,set_theme 原地切换)


def set_theme(name):
    if name not in THEMES:
        raise KeyError(f"未知主题 {name!r},可选 {sorted(THEMES)}")
    for k, v in THEMES[name].items():
        setattr(C, k, v)
    return C


# ----------------------------------------------------------------------------- 缓动
def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def ease(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)            # smoothstep


def ease_back(p):
    p = clamp(p)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


def appear(lt, t0, dur=0.55):
    """alpha 0->1,t0 起 dur 秒淡入。"""
    return ease((lt - t0) / dur)


def rgba(color, a):
    r, g, b = mcolors.to_rgb(color)
    return (r, g, b, clamp(a))


# ----------------------------------------------------------------------------- 画布
def overlay(fig, dx=0.0, dy=0.0):
    """竖屏 9x16 逻辑坐标的全幅覆盖层(空白背景)。dx/dy 为震屏偏移。"""
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(dx, 9 + dx)
    ax.set_ylim(dy, 16 + dy)
    ax.axis("off")
    return ax


# ----------------------------------------------------------------------------- 文本原语
def T(ax, x, y, s, lt, t0, size, color=None, ha="center", weight="normal",
      dur=0.55, dy=0.32, z=7):
    """淡入 + 上浮文本(原 animate.T)。"""
    color = color or C.WHITE
    a = appear(lt, t0, dur)
    if a <= 0.003:
        return
    yy = y - dy * (1 - ease((lt - t0) / dur))
    ax.text(x, yy, s, color=rgba(color, a), fontsize=size, ha=ha, va="center",
            weight=weight, zorder=z)


def boxed(ax, x, y, s, lt, t0, size, color=None, ha="center", dur=0.6):
    """圆角框答案,弹一下淡入(原 animate.boxed)。"""
    color = color or C.GOLD
    a = appear(lt, t0, dur)
    if a <= 0.003:
        return
    pop_ = 0.94 + 0.06 * ease((lt - t0) / dur)
    ax.text(x, y, s, color=rgba(color, a), fontsize=size * pop_, ha=ha, va="center",
            weight="bold", zorder=8,
            bbox=dict(boxstyle="round,pad=0.55", fc=rgba(color, 0.12 * a),
                      ec=rgba(color, 0.85 * a), lw=1.6))


def chip(ax, x, y, label, color, lt, t0, size=17):
    """圆形小标号,如 ①。"""
    a = appear(lt, t0, 0.5)
    if a <= 0.003:
        return
    ax.text(x, y, label, color=rgba(C.BG, a), fontsize=size, ha="center", va="center",
            weight="bold", zorder=8,
            bbox=dict(boxstyle="circle,pad=0.34", fc=rgba(color, a), ec="none"))


def style_graph(gax, title=None, tcolor=None):
    """统一的图象面板风格。"""
    gax.set_facecolor(C.GPANEL)
    for sp in ("top", "right"):
        gax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        gax.spines[sp].set_color(C.GSPINE)
    gax.tick_params(colors=C.MUTED, labelsize=8, length=3)
    gax.grid(True, color=C.GRID, lw=0.6, alpha=0.5)
    if title:
        gax.set_title(title, color=tcolor or C.WHITE, fontsize=12, pad=6)
