# -*- coding: utf-8 -*-
"""
趣味版「小球闯关」(竖屏 9:16, ~42s) —— 主攻第③问
游戏综艺感:BOSS关 -> 技能①化简 -> 技能②看图(小球滚山谷) -> 通关得证(撒花) -> 引导
吉祥物 / 小球 / 撒花 / 血条 全部用 matplotlib 手画(无字体乱码风险)。

Usage:
  python animate_fun.py --mascot              # 表情测试图
  python animate_fun.py --at 20 --out qa.png  # 单帧 QA
  python animate_fun.py                        # 全部帧 -> frames_fun/
"""
import argparse
import math
import os
import random

import matplotlib.pyplot as plt
import matplotlib.patches as mp
import numpy as np

import animate as A
from mascot import draw_mascot   # 固定角色「球球」: 单一事实来源(改角色只改 mascot.py)

# ----------------------------------------------------------------------------- config
W, H, DPI = 10.8, 19.2, 100          # 1080 x 1920
FPS = 24
FRAMES_DIR = "frames_fun"
RED = "#ff5a6a"
HP = "#7CFC9B"
HPTRACK = "#0b0e22"   # 进度条底槽(浅色主题可覆盖)

random.seed(7)
CONFETTI = []
_pal = [A.GOLD, A.GREEN, A.BLUE, A.PINK, RED, "#ffffff", "#c4b5fd"]
for _i in range(70):
    ang = random.uniform(0, 2 * math.pi)
    spd = random.uniform(2.2, 7.5)
    CONFETTI.append(dict(
        vx=math.cos(ang) * spd * random.uniform(0.6, 1.0),
        vy=abs(math.sin(ang)) * spd + random.uniform(1.5, 4.0),  # bias upward
        x0=4.5 + random.uniform(-1.2, 1.2),
        col=random.choice(_pal),
        sz=random.uniform(50, 150),
    ))

# ----------------------------------------------------------------------------- helpers
def overlay(fig, dx=0.0, dy=0.0):
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(dx, 9 + dx)
    ax.set_ylim(dy, 16 + dy)
    ax.axis("off")
    return ax

def ease_back(p):
    p = A.clamp(p)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2

def shake(lt, t0, dur=0.45, amp=0.12):
    if t0 <= lt < t0 + dur:
        k = 1 - (lt - t0) / dur
        return amp * k * math.sin(45 * (lt - t0)), amp * k * math.cos(38 * (lt - t0))
    return 0.0, 0.0

def PT(ax, x, y, s, lt, t0, size, color=A.WHITE, ha="center", dur=0.36, weight="bold"):
    p = A.clamp((lt - t0) / dur)
    if p <= 0.001:
        return
    sc = ease_back(p)
    a = A.clamp(p / 0.5)
    ax.text(x, y, s, color=A.rgba(color, a), fontsize=size * (0.6 + 0.4 * sc),
            ha=ha, va="center", weight=weight, zorder=8)

def tag(ax, x, y, s, color, lt, t0, size=20, tc=None, ha="center"):
    a = A.appear(lt, t0, 0.3)
    if a <= 0.003:
        return
    ax.text(x, y, s, color=A.rgba(tc or A.BG, a), fontsize=size, ha=ha, va="center",
            weight="bold", zorder=8,
            bbox=dict(boxstyle="round,pad=0.4", fc=A.rgba(color, a), ec="none"))

def score_pop(ax, x, y, lt, t0, text="+100", color=A.GOLD):
    p = (lt - t0) / 1.3
    if p <= 0 or p >= 1:
        return
    a = 1 - p
    ax.text(x, y + 1.2 * A.ease(A.clamp(p)), text, color=A.rgba(color, a), fontsize=26,
            ha="center", va="center", weight="bold", zorder=9)

def hp_bar(ax, frac, lt):
    a = A.appear(lt, 0.1, 0.4)
    if a <= 0.02:
        return
    x, y, w, h = 0.7, 15.2, 5.3, 0.46
    ax.add_patch(mp.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                 fc=A.rgba(HPTRACK, a), ec=A.rgba(A.GRID, a), lw=1.5, zorder=7))
    fillcol = HP if frac > 0.55 else (A.GOLD if frac > 0.3 else RED)
    ax.add_patch(mp.FancyBboxPatch((x + 0.08, y + 0.08), max(0.001, (w - 0.16) * frac), h - 0.16,
                 boxstyle="round,pad=0.04", fc=A.rgba(fillcol, a), ec="none", zorder=8))
    ax.text(x + w + 0.35, y + h / 2, f"挑战进度 {int(round(frac*100))}%",
            color=A.rgba(A.WHITE, a), fontsize=15, ha="left", va="center", weight="bold", zorder=9)

def confetti(ax, lt, t0):
    tau = lt - t0
    if tau <= 0:
        return
    xs, ys, cs, ss = [], [], [], []
    for c in CONFETTI:
        x = c["x0"] + c["vx"] * tau
        y = 8.2 + c["vy"] * tau - 4.6 * tau * tau
        if y < -1:
            continue
        xs.append(x); ys.append(y); cs.append(c["col"]); ss.append(c["sz"])
    if xs:
        a = A.clamp(1.3 - tau / 2.6)
        ax.scatter(xs, ys, s=ss, c=cs, marker="s", alpha=a, zorder=9, linewidths=0)

# ----------------------------------------------------------------------------- mascot
# 角色「球球」已抽到 mascot.py(单一事实来源);见顶部 `from mascot import draw_mascot`。

# ----------------------------------------------------------------------------- rolling ball
def ball_x(lt):
    # rolls in from left into the valley during lt 1.5..5.5, then settles & bobs
    p = A.clamp((lt - 1.5) / 4.0)
    xe = A.ease(p)
    x = 0.02 + (0.89 - 0.02) * xe
    if lt > 5.5:
        x = 0.89 + 0.05 * math.sin((lt - 5.5) * 2.0) * math.exp(-(lt - 5.5) * 0.6)
    return x

def draw_ball(gax, lt):
    if lt < 1.4:
        return
    bx = ball_x(lt)
    by = A.g3(bx)
    # trail
    for k in range(1, 6):
        tx = ball_x(lt - 0.06 * k)
        gax.scatter([tx], [A.g3(tx)], s=520 - 70 * k, color=A.rgba(A.GREEN, 0.10),
                    zorder=4, linewidths=0)
    # glow + core
    for sz, al in ((2600, 0.10), (1500, 0.18), (820, 0.34)):
        gax.scatter([bx], [by], s=sz, color=A.rgba(A.GREEN, al), zorder=5, linewidths=0)
    gax.scatter([bx], [by], s=360, color="#d8fff0", edgecolors=A.GREEN, linewidths=2, zorder=6)

def big_graph(gax, lt):
    A.style_graph(gax, None)
    xs = np.linspace(0, 1.42, 500)
    pc = A.ease(A.clamp((lt - 0.3) / 1.4))
    nc = max(2, int(len(xs) * pc))
    gax.plot(xs[:nc], A.g3(xs[:nc]), color=A.GREEN, lw=3.2)
    gax.axhline(0, color="#4a5080", lw=1.0)
    z1, z2 = math.pi / 12, 5 * math.pi / 12
    ba = A.appear(lt, 5.6)
    if ba > 0.2:
        gax.axvspan(z1, z2, color=A.rgba(A.GREEN, 0.10 * ba))
        for z, lab, dxo, hao in ((z1, r"$\frac{\pi}{12}$", 3, "left"),
                                 (z2, r"$\frac{5\pi}{12}$", -3, "right")):
            gax.axvline(z, color=A.rgba(A.MUTED, 0.7 * ba), lw=1.0, ls=":")
            gax.annotate(lab, (z, 0), xytext=(dxo, 10), textcoords="offset points",
                         color=A.rgba(A.MUTED, ba), fontsize=13, ha=hao)
    draw_ball(gax, lt)
    x1, x2, x3, L = A.P3
    p13 = ease_back(A.clamp((lt - 6.5) / 0.5))
    if lt > 6.5:
        gax.axhline(L, color=A.rgba(RED, 0.45), lw=1.2, ls="--")
        for xv, lab in ((x1, r"$x_1$"), (x3, r"$x_3$")):
            gax.scatter([xv], [A.g3(xv)], s=240 * p13, color=RED, zorder=7, edgecolors="white", linewidths=1.5)
            gax.annotate(lab, (xv, A.g3(xv)), xytext=(-6, -26), textcoords="offset points",
                         color=RED, fontsize=15, weight="bold")
    if lt > 9.0:
        p2 = ease_back(A.clamp((lt - 9.0) / 0.5))
        gax.scatter([x2], [A.g3(x2)], s=240 * p2, color=A.GOLD, zorder=7, edgecolors="white", linewidths=1.5)
        gax.annotate(r"$x_2$", (x2, A.g3(x2)), xytext=(-6, 16), textcoords="offset points",
                     color=A.GOLD, fontsize=15, weight="bold")
    gax.set_xlim(0, 1.42)
    gax.set_ylim(-10.5, 6)
    gax.tick_params(labelsize=10)

# ----------------------------------------------------------------------------- scenes
def s_hook(fig, ax, lt, dur):
    tag(ax, 4.5, 13.0, "BOSS 关", RED, lt, 0.5, 22)
    PT(ax, 4.5, 11.7, "压轴 · 第 ③ 问", lt, 0.2, 40, A.WHITE)
    A.T(ax, 4.5, 10.3, "BOSS 技能", lt, 1.2, 18, RED, ha="center", dur=0.3)
    A.T(ax, 4.5, 9.3, r"$g(x_1)=g'(x_2)=g(x_3)<0$", lt, 1.5, 20, A.WHITE, ha="center", dur=0.35)
    a = A.appear(lt, 2.3, 0.4)
    if a > 0.02:
        ax.text(4.5, 7.9, r"求证 $x_1+x_2+x_3>\dfrac{3\pi}{4}$", color=A.rgba(A.GOLD, a),
                fontsize=24, ha="center", va="center", weight="bold", zorder=8,
                bbox=dict(boxstyle="round,pad=0.5", fc=A.rgba(A.GOLD, 0.12 * a),
                          ec=A.rgba(A.GOLD, 0.85 * a), lw=1.8))
    draw_mascot(ax, 4.5, 4.6, 1.05, "panic", lt)
    A.T(ax, 6.5, 5.6, "啊这…", lt, 1.0, 20, A.MUTED, ha="left", dur=0.3)

def s_skill1(fig, ax, lt, dur):
    tag(ax, 4.5, 13.7, "技能① 化简", A.BLUE, lt, 0.1, 22)
    A.T(ax, 4.5, 12.0, r"$a=0:\ f(x)=\mathrm{e}^{x}\cos 3x$", lt, 0.5, 21, A.WHITE, ha="center", dur=0.35)
    A.T(ax, 4.5, 10.6, r"$g(x)=2f(x)+f'(x)$", lt, 1.3, 21, A.WHITE, ha="center", dur=0.35)
    a = A.appear(lt, 2.4, 0.4)
    if a > 0.02:
        ax.text(4.5, 8.9, r"$=3\sqrt{2}\,\mathrm{e}^{x}\cos\!\left(3x+\dfrac{\pi}{4}\right)$",
                color=A.rgba(A.GREEN, a), fontsize=25, ha="center", va="center", weight="bold", zorder=8,
                bbox=dict(boxstyle="round,pad=0.55", fc=A.rgba(A.GREEN, 0.12 * a),
                          ec=A.rgba(A.GREEN, 0.9 * a), lw=1.8))
    score_pop(ax, 6.6, 9.2, lt, 2.6)
    expr = "cool" if lt > 4.3 else ("idea" if lt > 2.6 else "think")   # 想→灵光→自信😎
    draw_mascot(ax, 2.1, 4.4, 1.0, expr, lt)
    PT(ax, 5.4, 4.2, "一步打穿!", lt, 3.2, 22, A.GOLD)

def s_graph(fig, ax, lt, dur):
    tag(ax, 4.5, 14.2, "技能② 看图秒懂", A.GREEN, lt, 0.1, 21)
    gax = fig.add_axes([0.08, 0.40, 0.84, 0.40])
    big_graph(gax, lt)
    a1 = A.appear(lt, 7.2, 0.4)
    if a1 > 0.02:
        ax.text(4.5, 4.7, r"$x_1+x_3>\dfrac{\pi}{2}$", color=A.rgba(RED, a1), fontsize=24,
                ha="center", va="center", weight="bold", zorder=8)
        A.T(ax, 4.5, 3.8, r"($\mathrm{e}^{x}$ 放大 → 图象右偏)", lt, 7.6, 16, A.MUTED, ha="center", dur=0.4)
        score_pop(ax, 6.7, 4.9, lt, 7.2)
    a2 = A.appear(lt, 9.4, 0.4)
    if a2 > 0.02:
        ax.text(4.5, 2.8, r"$x_2>\dfrac{\pi}{4}$  (谷底附近)", color=A.rgba(A.GOLD, a2),
                fontsize=23, ha="center", va="center", weight="bold", zorder=8)
        score_pop(ax, 6.7, 2.9, lt, 9.4)
    draw_mascot(ax, 1.2, 1.4, 0.7, "love" if 7.0 <= lt <= 12.5 else "cheer", lt)   # 看图惊叹😲

def s_clear(fig, ax, lt, dur):
    # flash + confetti
    fl = A.clamp(1 - lt / 0.5)
    if fl > 0.01:
        ax.add_patch(mp.Rectangle((0, 0), 9, 16, color=A.rgba("#ffffff", 0.5 * fl), zorder=10))
    confetti(ax, lt, 0.15)
    PT(ax, 4.5, 13.2, "通 关 !", lt, 0.2, 52, A.GOLD)
    a1 = A.appear(lt, 0.7, 0.35)
    if a1 > 0.02:
        ax.text(4.5, 10.9, r"$x_1+x_3>\dfrac{\pi}{2}$", color=A.rgba(RED, a1), fontsize=23,
                ha="center", va="center", weight="bold", zorder=8)
    a2 = A.appear(lt, 1.2, 0.35)
    if a2 > 0.02:
        ax.text(4.5, 9.6, r"$x_2>\dfrac{\pi}{4}$", color=A.rgba(A.GOLD, a2), fontsize=23,
                ha="center", va="center", weight="bold", zorder=8)
    p = A.clamp((lt - 2.0) / 0.45)
    if p > 0.001:
        sc = ease_back(p)
        ax.text(4.5, 7.6, r"$x_1+x_2+x_3>\dfrac{\pi}{2}+\dfrac{\pi}{4}=\dfrac{3\pi}{4}$",
                color=A.rgba(A.GREEN, A.clamp(p / 0.5)), fontsize=22 * (0.7 + 0.3 * sc),
                ha="center", va="center", weight="bold", zorder=8,
                bbox=dict(boxstyle="round,pad=0.6", fc=A.rgba(A.GREEN, 0.14),
                          ec=A.rgba(A.GREEN, 0.9), lw=2.0))
    # drawn check + 得证
    cm = A.appear(lt, 3.2, 0.3)
    if cm > 0.1:
        ax.plot([3.5, 3.9, 4.6], [5.55, 5.15, 6.1], color=A.rgba(A.GREEN, cm), lw=7,
                solid_capstyle="round", solid_joinstyle="round", zorder=9)
    PT(ax, 5.4, 5.5, "得证", lt, 3.2, 38, A.GREEN)
    draw_mascot(ax, 4.5, 2.4, 0.95, "thumbsup" if lt > 3.0 else "cheer", lt)   # 得证比赞👍

def s_cta(fig, ax, lt, dur):
    gax = fig.add_axes([0.07, 0.12, 0.86, 0.20])
    gax.axis("off"); gax.set_xlim(0, math.pi / 2); gax.set_ylim(-3.4, 3.4)
    xs = np.linspace(0, math.pi / 2, 300)
    gax.plot(xs, np.exp(xs) * np.cos(3 * xs), color=A.rgba(A.GREEN, 0.22), lw=2.2)
    PT(ax, 4.5, 12.0, "完整 ①②③ 问解析", lt, 0.2, 28, A.WHITE)
    a = A.appear(lt, 0.9, 0.4)
    if a > 0.02:
        ax.text(4.5, 10.4, "→ 主页 / 合集", color=A.rgba(A.BLUE, a), fontsize=26, ha="center",
                va="center", weight="bold", zorder=8,
                bbox=dict(boxstyle="round,pad=0.5", fc=A.rgba(A.BLUE, 0.12 * a),
                          ec=A.rgba(A.BLUE, 0.8 * a), lw=1.6))
    A.T(ax, 4.5, 8.9, "点赞收藏 · 通关下一题", lt, 1.5, 19, A.MUTED, ha="center", dur=0.4)
    draw_mascot(ax, 4.5, 5.2, 1.0, "wave", lt)

# ----------------------------------------------------------------------------- timeline
TIMELINE = [
    ("hook",   s_hook,   5.0),
    ("skill1", s_skill1, 7.0),
    ("graph",  s_graph,  18.0),
    ("clear",  s_clear,  7.0),
    ("cta",    s_cta,    5.0),
]
TOTAL = sum(d for _, _, d in TIMELINE)   # 42s

def progress_frac(gt):
    pts = [(0, 0.0), (5, 0.12), (12, 0.42), (30, 0.86), (35, 1.0), (TOTAL, 1.0)]
    for (t0, f0), (t1, f1) in zip(pts, pts[1:]):
        if gt <= t1:
            return f0 + (f1 - f0) * (gt - t0) / max(0.001, t1 - t0)
    return 1.0

def render_frame(fig, gt):
    fig.clf()
    fig.patch.set_facecolor(A.BG)
    acc = 0.0
    chosen = None
    for name, fn, d in TIMELINE:
        if gt < acc + d:
            chosen = (name, fn, d, acc); break
        acc += d
    if chosen is None:
        name, fn, d = TIMELINE[-1]; chosen = (name, fn, d, TOTAL - d)
    name, fn, d, start = chosen
    lt = A.clamp(gt - start, 0, d)
    dx, dy = (0.0, 0.0)
    if name == "hook":
        dx, dy = shake(lt, 0.2, 0.5, 0.14)
    elif name == "clear":
        dx, dy = shake(lt, 0.15, 0.5, 0.16)
    ax = overlay(fig, dx, dy)
    fn(fig, ax, lt, d)
    hp_bar(ax, progress_frac(gt), lt if name == "hook" else 1.0)

def render_mascot_sheet(fig):
    fig.patch.set_facecolor(A.BG)
    ax = overlay(fig)
    exprs = [("panic", "怕"), ("think", "想"), ("idea", "灵光"), ("happy", "开心"),
             ("cheer", "欢呼"), ("wave", "挥手")]
    for i, (e, lab) in enumerate(exprs):
        col = i % 2
        row = i // 2
        cx = 2.5 + col * 4.0
        cy = 12.5 - row * 4.2
        draw_mascot(ax, cx, cy, 1.2, e, 0.3)
        ax.text(cx, cy - 2.0, f"{lab} ({e})", color=A.WHITE, fontsize=18, ha="center", weight="bold")

# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", type=float, default=None)
    ap.add_argument("--out", default="qf.png")
    ap.add_argument("--fps", type=int, default=FPS)
    ap.add_argument("--dpi", type=int, default=DPI)
    ap.add_argument("--mascot", action="store_true")
    args = ap.parse_args()
    fig = plt.figure(figsize=(W, H), dpi=args.dpi)
    if args.mascot:
        render_mascot_sheet(fig)
        fig.savefig("qf_mascot.png", facecolor=A.BG)
        print("wrote qf_mascot.png")
        return
    if args.at is not None:
        render_frame(fig, args.at)
        fig.savefig(args.out, facecolor=A.BG)
        print("wrote", args.out, "at t=", args.at)
        return
    os.makedirs(FRAMES_DIR, exist_ok=True)
    n = int(TOTAL * args.fps)
    print(f"rendering {n} frames ({TOTAL}s @ {args.fps}fps)")
    for i in range(n):
        render_frame(fig, i / args.fps)
        fig.savefig(os.path.join(FRAMES_DIR, f"f{i:05d}.png"), facecolor=A.BG)
        if i % 50 == 0:
            print(f"  frame {i}/{n}")
    print("done frames")

if __name__ == "__main__":
    main()
