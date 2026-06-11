# -*- coding: utf-8 -*-
"""
角色模块「球球」—— 固定的卡通吉祥物(单一事实来源,所有视频共用)。
纯 matplotlib 手绘,无外部依赖,无字体乱码风险。

API:
  draw_mascot(ax, cx, cy, s, expr="happy", t=0.0)   # 在任意 axes 上画角色
  表情 expr ∈ EXPRESSIONS (14 种)

CLI:
  python mascot.py --sheet      # 角色设定图 -> mascot_sheet.png
  python mascot.py --sprites    # 透明素材   -> assets/mascot_<expr>.png
  python mascot.py              # 两者都出
"""
import argparse
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from matplotlib import font_manager

# ---- 锁定的设定(改这里 = 全系列统一改) ----
NAME = "球球"
TAGLINE = "数学闯关·吉祥物"
BODY = "#4ecdc4"     # 身体
OUT = "#2a9d96"      # 描边/手脚
CHEEK = "#ff9aa2"    # 腮红
EYE = "#11324a"      # 眼/嘴
SWEAT = "#6cc6ff"    # 汗滴/泪
BULB = "#ffcf6e"     # 灯泡/星星
BULB_BASE = "#caa23a"
FLAME = "#ff7a3c"    # 火苗
BG = "#0f1226"       # 设定图背景

EXPRESSIONS = ["happy", "panic", "think", "idea", "cheer", "wave", "point",
               "love", "wink", "cool", "cry", "angry", "dizzy", "thumbsup"]
_EXPR_CN = {"happy": "开心", "panic": "慌张", "think": "思考", "idea": "灵光",
            "cheer": "欢呼", "wave": "挥手", "point": "指向", "love": "惊叹",
            "wink": "俏皮", "cool": "自信", "cry": "沮丧", "angry": "燃",
            "dizzy": "懵", "thumbsup": "点赞"}

_cjk = [f for f in ("Microsoft YaHei", "SimHei", "SimSun")
        if f in {x.name for x in font_manager.fontManager.ttflist}]
plt.rcParams["font.sans-serif"] = _cjk + ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

_ARMS_UP = ("cheer", "happy", "wave", "love", "angry")


# ----------------------------------------------------------------------------- 小部件
def _drop(ax, x, y, r, color, z):
    """水滴(圆底 + 上尖):汗滴 / 泪。"""
    ax.add_patch(mp.Circle((x, y), r, color=color, zorder=z))
    ax.add_patch(mp.Polygon([[x - 0.77 * r, y + 0.15 * r], [x + 0.77 * r, y + 0.15 * r],
                 [x, y + 2.15 * r]], color=color, zorder=z))


def _star(ax, x, y, R, color, z, edge=BULB_BASE):
    pts = []
    for k in range(10):
        ang = math.pi / 2 + k * math.pi / 5
        rad = R if k % 2 == 0 else R * 0.42
        pts.append((x + rad * math.cos(ang), y + rad * math.sin(ang)))
    ax.add_patch(mp.Polygon(pts, closed=True, facecolor=color, edgecolor=edge, lw=1.2, zorder=z))


def _spiral(ax, x, y, R, color, z):
    xs, ys, n = [], [], 60
    for k in range(n + 1):
        th = k / n * 4 * math.pi
        r = R * k / n
        xs.append(x + r * math.cos(th)); ys.append(y + r * math.sin(th))
    ax.plot(xs, ys, color=color, lw=2.4, zorder=z, solid_capstyle="round")


def _flame(ax, x, y, s, z):
    ax.add_patch(mp.Polygon([[x - 0.32 * s, y], [x + 0.32 * s, y], [x, y + 0.95 * s]],
                 color=FLAME, zorder=z))
    ax.add_patch(mp.Polygon([[x - 0.16 * s, y + 0.06 * s], [x + 0.16 * s, y + 0.06 * s],
                 [x, y + 0.58 * s]], color=BULB, zorder=z + 1))


def _sunglasses(ax, cx, cy, s, ey, z):
    for sgn in (-1, 1):
        ax.add_patch(mp.FancyBboxPatch((cx + sgn * 0.36 * s - 0.30 * s, cy + ey - 0.22 * s),
                     0.60 * s, 0.40 * s, boxstyle="round,pad=0.02",
                     fc=EYE, ec="#05101c", lw=1.5, zorder=z))
    ax.plot([cx - 0.06 * s, cx + 0.06 * s], [cy + ey + 0.06 * s, cy + ey + 0.06 * s],
            color=EYE, lw=4, solid_capstyle="round", zorder=z)
    ax.plot([cx - 0.52 * s, cx - 0.40 * s], [cy + ey + 0.10 * s, cy + ey - 0.02 * s],
            color="white", lw=2, solid_capstyle="round", zorder=z + 1)


# ----------------------------------------------------------------------------- 角色
def draw_mascot(ax, cx, cy, s, expr="happy", t=0.0, z=6):
    """画一只「球球」。s=头半径(数据单位)。坐标系需大致等比(x、y 单位等长)。"""
    cy = cy + 0.05 * s * math.sin(2 * math.pi * t / 1.6)   # 轻微上下浮动
    # 脚
    for fx in (-0.40, 0.40):
        ax.add_patch(mp.Ellipse((cx + fx * s, cy - 1.02 * s), 0.34 * s, 0.20 * s,
                     color=OUT, zorder=z))
    # 手臂
    up = expr in _ARMS_UP
    for side, sx in (("l", -1), ("r", 1)):
        x0 = cx + sx * 0.92 * s
        if expr == "point" and side == "r":
            ax.plot([x0, x0 + 0.72 * s], [cy - 0.05 * s, cy + 0.06 * s],
                    color=OUT, lw=4.5, solid_capstyle="round", zorder=z)
        elif expr == "thumbsup" and side == "r":            # 举手 + 拳头 + 大拇指
            ax.plot([x0, x0 + 0.30 * s], [cy - 0.1 * s, cy + 0.55 * s],
                    color=OUT, lw=4.5, solid_capstyle="round", zorder=z)
            fx_, fy_ = x0 + 0.30 * s, cy + 0.72 * s
            ax.add_patch(mp.Ellipse((fx_ - 0.10 * s, fy_ + 0.27 * s), 0.22 * s, 0.36 * s,
                         angle=8, facecolor=BODY, edgecolor=OUT, lw=2.5, zorder=z))
            ax.add_patch(mp.Ellipse((fx_, fy_), 0.46 * s, 0.38 * s, facecolor=BODY,
                         edgecolor=OUT, lw=2.5, zorder=z + 0.05))
            for k in range(3):                               # 指节(蜷起的手指,拇指同侧)
                ky = fy_ + (0.09 - 0.09 * k) * s
                ax.plot([fx_ - 0.16 * s, fx_ - 0.03 * s], [ky, ky], color=OUT, lw=2,
                        solid_capstyle="round", zorder=z + 0.1)
        elif up and not (expr in ("wave",) and side == "l"):
            ax.plot([x0, x0 + sx * 0.45 * s], [cy - 0.1 * s, cy + 0.7 * s],
                    color=OUT, lw=4.5, solid_capstyle="round", zorder=z)
        else:
            ax.plot([x0, x0 + sx * 0.30 * s], [cy - 0.1 * s, cy - 0.5 * s],
                    color=OUT, lw=4.5, solid_capstyle="round", zorder=z)
    # 头
    ax.add_patch(mp.Circle((cx, cy), s, facecolor=BODY, edgecolor=OUT, lw=3, zorder=z + 1))
    # 腮红
    for chx in (-0.52, 0.52):
        ax.add_patch(mp.Circle((cx + chx * s, cy - 0.20 * s), 0.15 * s, color=CHEEK,
                     alpha=0.75, zorder=z + 2))
    # 眼睛
    ex, ey, er = 0.36 * s, 0.12 * s, 0.30 * s
    blink = (t % 2.7) < 0.12
    look = {"think": (-0.4, 0.5), "panic": (0, 0.5), "point": (0.55, 0.0)}.get(expr, (0, 0))
    if expr == "cool":
        _sunglasses(ax, cx, cy, s, ey, z + 3)
    else:
        for sgn in (-1, 1):
            gx, gy = cx + sgn * ex, cy + ey
            if expr == "love":
                _star(ax, gx, gy, 0.32 * s, BULB, z + 3)
            elif expr == "dizzy":
                _spiral(ax, gx, gy, 0.30 * s, EYE, z + 3)
            elif expr == "wink" and sgn == 1:                 # 右眼眨
                ax.add_patch(mp.Arc((gx, gy), 0.5 * s, 0.5 * s, angle=0, theta1=200,
                             theta2=340, color=EYE, lw=4, zorder=z + 3))
            elif expr in ("happy", "cheer", "thumbsup") or blink:
                ax.add_patch(mp.Arc((gx, gy), 0.5 * s, 0.5 * s, angle=0, theta1=20,
                             theta2=160, color=EYE, lw=4, zorder=z + 3))
            else:
                ax.add_patch(mp.Circle((gx, gy), er, facecolor="white", edgecolor=EYE,
                             lw=1.5, zorder=z + 3))
                pr = 0.15 * s if expr != "panic" else 0.10 * s
                ax.add_patch(mp.Circle((gx + look[0] * er, gy + look[1] * er), pr,
                             color=EYE, zorder=z + 4))
            if expr == "panic":     # 上挑眉
                ax.plot([gx - 0.22 * s, gx + 0.16 * s], [cy + 0.62 * s, cy + 0.72 * s],
                        color=OUT, lw=3, solid_capstyle="round", zorder=z + 4)
            if expr == "angry":     # 怒眉(内低外高)
                ax.plot([gx + sgn * 0.22 * s, gx - sgn * 0.20 * s], [cy + 0.70 * s, cy + 0.50 * s],
                        color=OUT, lw=3.5, solid_capstyle="round", zorder=z + 4)
    # 嘴
    mx, my = cx, cy - 0.42 * s
    if expr in ("happy", "cheer", "idea", "wave", "point", "love", "wink", "cool", "thumbsup"):
        ax.add_patch(mp.Arc((mx, my), 0.6 * s, 0.5 * s, angle=0, theta1=200, theta2=340,
                     color=EYE, lw=4, zorder=z + 3))
    elif expr == "panic":
        ax.add_patch(mp.Ellipse((mx, my - 0.05 * s), 0.28 * s, 0.34 * s,
                     facecolor=EYE, edgecolor="none", zorder=z + 3))
    elif expr == "angry":                                    # 张嘴吼
        ax.add_patch(mp.Ellipse((mx, my - 0.04 * s), 0.34 * s, 0.24 * s,
                     facecolor=EYE, edgecolor="none", zorder=z + 3))
    elif expr == "cry":                                      # 倒扣嘴(难过)
        ax.add_patch(mp.Arc((mx, my - 0.04 * s), 0.5 * s, 0.42 * s, angle=0, theta1=20,
                     theta2=160, color=EYE, lw=4, zorder=z + 3))
    elif expr == "dizzy":                                    # 波浪嘴
        xs = [mx - 0.22 * s + i * 0.088 * s for i in range(6)]
        ys = [my + (0.06 * s if i % 2 else -0.06 * s) for i in range(6)]
        ax.plot(xs, ys, color=EYE, lw=3, solid_capstyle="round", zorder=z + 3)
    else:  # think
        ax.plot([mx - 0.18 * s, mx + 0.18 * s], [my, my], color=EYE, lw=3.5,
                solid_capstyle="round", zorder=z + 3)
    # 配饰
    if expr == "panic":
        _drop(ax, cx + 1.02 * s, cy + 0.55 * s, 0.13 * s, SWEAT, z + 3)
    if expr == "cry":
        for sgn in (-1, 1):
            _drop(ax, cx + sgn * 0.36 * s, cy - 0.28 * s, 0.12 * s, SWEAT, z + 3)
    if expr == "idea":
        bx, by = cx, cy + 1.7 * s
        for ang in range(0, 360, 45):
            r1, r2 = 0.55 * s, 0.8 * s
            ax.plot([bx + r1 * math.cos(math.radians(ang)), bx + r2 * math.cos(math.radians(ang))],
                    [by + r1 * math.sin(math.radians(ang)), by + r2 * math.sin(math.radians(ang))],
                    color=BULB, lw=2.5, solid_capstyle="round", zorder=z + 2)
        ax.add_patch(mp.Circle((bx, by), 0.34 * s, facecolor=BULB, edgecolor=BULB_BASE,
                     lw=2, zorder=z + 3))
        ax.add_patch(mp.Rectangle((bx - 0.12 * s, by - 0.45 * s), 0.24 * s, 0.16 * s,
                     color=BULB_BASE, zorder=z + 3))
    if expr == "angry":
        _flame(ax, cx, cy + 1.0 * s, s, z + 2)
        _flame(ax, cx - 0.5 * s, cy + 0.95 * s, 0.6 * s, z + 2)
        _flame(ax, cx + 0.5 * s, cy + 0.95 * s, 0.6 * s, z + 2)
    if expr == "dizzy":
        for k, ang in enumerate((150, 90, 30)):
            sx_ = cx + 0.7 * s * math.cos(math.radians(ang))
            sy_ = cy + 1.25 * s + 0.18 * s * math.sin(math.radians(ang))
            _star(ax, sx_, sy_, 0.13 * s, BULB, z + 3)


# ----------------------------------------------------------------------------- 设定图
_SHEET_ORDER = ["idea", "angry", "dizzy", "love", "cool",
                "happy", "panic", "think", "wink", "cry",
                "cheer", "wave", "point", "thumbsup"]


def render_sheet(path="mascot_sheet.png"):
    fig = plt.figure(figsize=(16, 12), dpi=100)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 16); ax.set_ylim(0, 12); ax.axis("off")
    ax.text(0.6, 11.35, f"角色设定 · {NAME}", color="white", fontsize=32, weight="bold", va="center")
    ax.text(0.65, 10.75, f"{TAGLINE} · 14 表情", color="#9aa3c8", fontsize=17, va="center")
    ax.plot([0.6, 15.4], [10.35, 10.35], color="#2a2f57", lw=1.5)
    xs = [1.7, 4.55, 7.4, 10.25, 13.1]
    ys = [8.5, 5.6, 2.7]
    for i, e in enumerate(_SHEET_ORDER):
        gx, gy = xs[i % 5], ys[i // 5]
        draw_mascot(ax, gx, gy, 0.72, e, 0.3)
        ax.text(gx, gy - 1.5, f"{_EXPR_CN[e]} ({e})", color="#d7dcff", fontsize=13,
                ha="center", weight="bold")
    sw = [("身体", BODY), ("描边", OUT), ("腮红", CHEEK), ("眼/嘴", EYE), ("点缀", SWEAT)]
    for i, (lab, col) in enumerate(sw):
        x = 0.7 + i * 1.7
        ax.add_patch(mp.FancyBboxPatch((x, 0.35), 0.42, 0.42, boxstyle="round,pad=0.03",
                     fc=col, ec="#2a2f57", lw=1, zorder=3))
        ax.text(x + 0.55, 0.7, lab, color="white", fontsize=10, va="center")
        ax.text(x + 0.55, 0.42, col, color="#9aa3c8", fontsize=9, va="center")
    fig.savefig(path, facecolor=BG)
    plt.close(fig)
    print("wrote", path)


def render_sprites(outdir="assets"):
    os.makedirs(outdir, exist_ok=True)
    for e in EXPRESSIONS:
        fig = plt.figure(figsize=(6, 7), dpi=120)
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_aspect("equal"); ax.axis("off")
        ax.set_xlim(-2.8, 2.8); ax.set_ylim(-2.4, 3.8)
        draw_mascot(ax, 0, 0, 1.0, e, 0.3)
        p = os.path.join(outdir, f"mascot_{e}.png")
        fig.savefig(p, transparent=True, bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)
        print("wrote", p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--sprites", action="store_true")
    args = ap.parse_args()
    if not args.sheet and not args.sprites:
        args.sheet = args.sprites = True
    if args.sheet:
        render_sheet()
    if args.sprites:
        render_sprites()


if __name__ == "__main__":
    main()
