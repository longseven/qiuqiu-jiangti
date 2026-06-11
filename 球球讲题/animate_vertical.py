# -*- coding: utf-8 -*-
"""
导数压轴题 动画讲解 —— 竖屏 (9:16) 版
Reuses math + helpers + colors from animate.py; only the layout is rewritten
(header -> stacked formula steps -> answer -> full-width graph at the bottom).

Usage:
  python animate_vertical.py --at 31 --out qa.png   # single frame QA
  python animate_vertical.py                         # all frames -> frames_v/
"""
import argparse
import math
import os

import matplotlib.pyplot as plt
import numpy as np

import animate as A   # reuses fonts/rcParams, colors, helpers, math fns, P3, FUNC

# ----------------------------------------------------------------------------- config
W, H, DPI = 10.8, 19.2, 100          # 1080 x 1920 (portrait)
FPS = 24
FRAMES_DIR = "frames_v"

def overlay(fig):
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 9)            # 9 wide x 16 tall, 120 px / unit
    ax.set_ylim(0, 16)
    ax.axis("off")
    return ax

def pbar(ax, gt, total, color):
    p = A.clamp(gt / total)
    ax.add_patch(plt.Rectangle((0.5, 0.30), 8.0, 0.06, color=A.GRID, zorder=1))
    ax.add_patch(plt.Rectangle((0.5, 0.30), 8.0 * p, 0.06, color=color, zorder=2))

def header(ax, lt, idx, title, color, tsize=24):
    A.chip(ax, 0.75, 15.25, idx, color, lt, 0.0)
    A.T(ax, 1.35, 15.25, title, lt, 0.1, tsize, color, weight="bold")
    ax.plot([0.5, 8.5], [14.75, 14.75], color=A.GRID, lw=1.3)

# ----------------------------------------------------------------------------- graphs
def graph_part1(gax, lt):
    A.style_graph(gax, r"$f(x)$ 与切线 @ $x=\frac{\pi}{2}$", A.BLUE)
    xs = np.linspace(1.15, 1.85, 400)
    pc = A.ease(A.clamp((lt - 1.0) / 1.8))
    nc = max(2, int(len(xs) * pc))
    gax.plot(xs[:nc], A.f1(xs[:nc]), color=A.BLUE, lw=2.6)
    pt = A.ease(A.clamp((lt - 4.0) / 1.6))
    half = 0.34 * pt
    xt = np.linspace(math.pi / 2 - half, math.pi / 2 + half, 50)
    gax.plot(xt, A.tangent1(xt), color=A.GOLD, lw=2.4, ls="--")
    if A.appear(lt, 3.0) > 0.2:
        gax.plot([math.pi / 2], [0], "o", color=A.PINK, ms=9, zorder=5)
        gax.annotate(r"$\left(\frac{\pi}{2},0\right)$", (math.pi / 2, 0),
                     textcoords="offset points", xytext=(8, -18), color=A.PINK, fontsize=12)
    gax.set_xlim(1.15, 1.85)
    gax.set_ylim(-5, 8)

def graph_part2(gax, lt):
    A.style_graph(gax, r"$h(t)=\frac{2\cos t-1}{\mathrm{e}^{t}}$", A.GOLD)
    ts = np.linspace(0, math.pi / 2, 400)
    pc = A.ease(A.clamp((lt - 2.6) / 1.8))
    nc = max(2, int(len(ts) * pc))
    gax.plot(ts[:nc], A.h2(ts[:nc]), color=A.GOLD, lw=2.8)
    top, bot = 1.0, -math.exp(-math.pi / 2)
    ba = A.appear(lt, 4.4)
    if ba > 0.2:
        gax.axhspan(bot, top, color=A.rgba(A.GOLD, 0.10 * ba))
        gax.axhline(top, color=A.rgba(A.GREEN, 0.8 * ba), lw=1.3, ls=":")
        gax.axhline(bot, color=A.rgba(A.GREEN, 0.8 * ba), lw=1.3, ls=":")
        gax.plot([0], [top], "o", mfc="#12173a", mec=A.GOLD, ms=7)
        gax.plot([math.pi / 2], [bot], "o", mfc="#12173a", mec=A.GOLD, ms=7)
        gax.annotate(r"$1$", (0, top), xytext=(6, 5), textcoords="offset points",
                     color=A.GREEN, fontsize=11)
        gax.annotate(r"$-\mathrm{e}^{-\frac{\pi}{2}}$", (math.pi / 2, bot),
                     xytext=(-60, 16), textcoords="offset points", color=A.GREEN, fontsize=12)
        gax.text(0.78, 0.42, "有解区间(应排除)", color=A.rgba(A.MUTED, ba), fontsize=10,
                 ha="center", va="center")
    gax.set_xlim(0, math.pi / 2)
    gax.set_ylim(-0.55, 1.2)

def graph_part3(gax, lt):
    A.style_graph(gax, r"$g(x)=3\sqrt{2}\,\mathrm{e}^{x}\cos(3x+\frac{\pi}{4})$", A.GREEN)
    xs = np.linspace(0, 1.42, 500)
    pc = A.ease(A.clamp((lt - 1.5) / 1.8))
    nc = max(2, int(len(xs) * pc))
    gax.plot(xs[:nc], A.g3(xs[:nc]), color=A.GREEN, lw=2.6)
    gax.axhline(0, color="#4a5080", lw=1.0)
    z1, z2 = math.pi / 12, 5 * math.pi / 12
    ba = A.appear(lt, 3.0)
    if ba > 0.2:
        gax.axvspan(z1, z2, color=A.rgba(A.GREEN, 0.08 * ba))
        for z, lab in ((z1, r"$\frac{\pi}{12}$"), (z2, r"$\frac{5\pi}{12}$")):
            gax.axvline(z, color=A.rgba(A.MUTED, 0.7 * ba), lw=1.0, ls=":")
            gax.annotate(lab, (z, 0), xytext=(2, 9), textcoords="offset points",
                         color=A.rgba(A.MUTED, ba), fontsize=11)
    x1, x2, x3, L = A.P3
    pa = A.appear(lt, 4.2)
    if pa > 0.2:
        gax.axhline(L, color=A.rgba(A.PINK, 0.5 * pa), lw=1.0, ls="--")
        for xv, lab, col in ((x1, r"$x_1$", A.PINK), (x2, r"$x_2$", A.GOLD), (x3, r"$x_3$", A.PINK)):
            yv = A.g3(xv)
            gax.plot([xv], [yv], "o", color=A.rgba(col, pa), ms=9, zorder=6)
            gax.annotate(lab, (xv, yv), xytext=(-5, -18), textcoords="offset points",
                         color=A.rgba(col, pa), fontsize=12)
    gax.set_xlim(0, 1.42)
    gax.set_ylim(-10.5, 6)

# ----------------------------------------------------------------------------- scenes
def s_title(fig, ax, lt, dur):
    gax = fig.add_axes([0.07, 0.20, 0.86, 0.26])
    gax.axis("off")
    gax.set_xlim(0, math.pi / 2)
    gax.set_ylim(-3.4, 3.4)
    xs = np.linspace(0, math.pi / 2, 400)
    n = max(2, int(len(xs) * A.ease(A.clamp(lt / 2.2))))
    gax.plot(xs[:n], np.exp(xs[:n]) * np.cos(3 * xs[:n]), color=A.rgba(A.BLUE, 0.35), lw=2.4)
    A.T(ax, 4.5, 12.4, "导数压轴题", lt, 0.2, 50, A.WHITE, ha="center", weight="bold")
    A.T(ax, 4.5, 11.3, "动画精讲 · 竖屏版", lt, 0.6, 26, A.MUTED, ha="center")
    A.T(ax, 4.5, 9.7, A.FUNC, lt, 1.0, 22, A.BLUE, ha="center")
    A.T(ax, 4.5, 8.8, "切线  ·  零点  ·  不等式", lt, 1.6, 19, A.MUTED, ha="center")

def s_problem(fig, ax, lt, dur):
    A.T(ax, 0.6, 15.3, "题目", lt, 0.0, 24, A.WHITE, weight="bold")
    ax.plot([0.5, 8.5], [14.8, 14.8], color=A.GRID, lw=1.3)
    A.T(ax, 4.5, 13.8, A.FUNC, lt, 0.3, 21, A.BLUE, ha="center")
    A.chip(ax, 0.95, 12.0, "1", A.BLUE, lt, 1.3)
    A.T(ax, 1.6, 12.0, r"当 $a=\mathrm{e}^{-\pi}$ 时,求 $f(x)$ 在", lt, 1.4, 18, A.WHITE)
    A.T(ax, 1.6, 11.3, r"点 $\left(\frac{\pi}{2},f(\frac{\pi}{2})\right)$ 处的切线方程", lt, 1.6, 18, A.WHITE)
    A.chip(ax, 0.95, 9.6, "2", A.GOLD, lt, 2.9)
    A.T(ax, 1.6, 9.6, r"若 $f(x)$ 在 $\left(0,\frac{\pi}{4}\right)$ 上没有零点,", lt, 3.0, 18, A.WHITE)
    A.T(ax, 1.6, 8.9, r"求实数 $a$ 的取值范围", lt, 3.2, 18, A.WHITE)
    A.chip(ax, 0.95, 7.0, "3", A.GREEN, lt, 4.4)
    A.T(ax, 1.6, 7.2, r"当 $a=0$ 时,$g(x)=2f(x)+f'(x)$,", lt, 4.5, 18, A.WHITE)
    A.T(ax, 1.6, 6.5, r"若 $x_1<x_2<x_3\in\left(0,\frac{\pi}{2}\right)$ 满足", lt, 4.8, 18, A.WHITE)
    A.T(ax, 1.6, 5.8, r"$g(x_1)=g'(x_2)=g(x_3)<0$,", lt, 5.1, 18, A.WHITE)
    A.T(ax, 1.6, 5.1, r"证明 $x_1+x_2+x_3>\frac{3\pi}{4}$", lt, 5.4, 18, A.PINK)

def s_part1(fig, ax, lt, dur):
    header(ax, lt, "1", "切线方程", A.BLUE)
    A.T(ax, 4.5, 13.7, r"$a=\mathrm{e}^{-\pi}$", lt, 0.4, 20, A.GOLD, ha="center")
    A.T(ax, 4.5, 12.7, r"$f(x)=\mathrm{e}^{x}\cos 3x-\mathrm{e}^{-\pi}\mathrm{e}^{3x}\cos x$", lt, 0.7, 19, A.WHITE, ha="center")
    A.T(ax, 4.5, 11.6, r"$f'(x)=\mathrm{e}^{x}(\cos 3x-3\sin 3x)$", lt, 1.6, 19, A.MUTED, ha="center")
    A.T(ax, 4.5, 10.85, r"$-\,\mathrm{e}^{-\pi}\mathrm{e}^{3x}(3\cos x-\sin x)$", lt, 2.1, 19, A.MUTED, ha="center")
    A.T(ax, 4.5, 9.7, r"$f\!\left(\frac{\pi}{2}\right)=0,\quad f'\!\left(\frac{\pi}{2}\right)=4\,\mathrm{e}^{\frac{\pi}{2}}$", lt, 3.0, 20, A.BLUE, ha="center")
    A.boxed(ax, 4.5, 8.3, r"$y=4\,\mathrm{e}^{\frac{\pi}{2}}\!\left(x-\frac{\pi}{2}\right)$", lt, 4.2, 23, A.GOLD)
    gax = fig.add_axes([0.12, 0.045, 0.78, 0.33])
    graph_part1(gax, lt)

def s_part2(fig, ax, lt, dur):
    header(ax, lt, "2", "零点与取值范围", A.GOLD)
    A.T(ax, 4.5, 13.8, r"$f(x)=0\ \Rightarrow\ \mathrm{e}^{x}\cos 3x=a\,\mathrm{e}^{3x}\cos x$", lt, 0.4, 18, A.WHITE, ha="center")
    A.T(ax, 4.5, 12.85, r"$\cos 3x=\cos x\,(2\cos 2x-1)$", lt, 1.3, 18, A.MUTED, ha="center")
    A.T(ax, 4.5, 11.95, r"$\Rightarrow\ \dfrac{2\cos 2x-1}{\mathrm{e}^{2x}}=a$", lt, 1.9, 18, A.MUTED, ha="center")
    A.T(ax, 4.5, 10.85, r"$t=2x:\ h(t)=\dfrac{2\cos t-1}{\mathrm{e}^{t}}$   (递减)", lt, 2.7, 18, A.WHITE, ha="center")
    A.T(ax, 4.5, 9.7, r"$h(0)=1,\quad h\!\left(\frac{\pi}{2}\right)=-\mathrm{e}^{-\frac{\pi}{2}}$", lt, 3.6, 18, A.WHITE, ha="center")
    A.boxed(ax, 4.5, 8.3, r"$a\in\left(-\infty,-\mathrm{e}^{-\frac{\pi}{2}}\right]\cup\left[1,+\infty\right)$", lt, 4.6, 20, A.GOLD)
    gax = fig.add_axes([0.12, 0.045, 0.78, 0.33])
    graph_part2(gax, lt)

def s_part3(fig, ax, lt, dur):
    header(ax, lt, "3", r"证明 $x_1{+}x_2{+}x_3>\frac{3\pi}{4}$", A.GREEN, tsize=22)
    A.T(ax, 4.5, 13.7, r"$a=0:\ f(x)=\mathrm{e}^{x}\cos 3x$", lt, 0.4, 19, A.WHITE, ha="center")
    A.T(ax, 4.5, 12.6, r"$g(x)=2f(x)+f'(x)$", lt, 1.2, 19, A.GREEN, ha="center")
    A.T(ax, 4.5, 11.75, r"$=3\sqrt{2}\,\mathrm{e}^{x}\cos\!\left(3x+\frac{\pi}{4}\right)$", lt, 1.6, 19, A.GREEN, ha="center")
    A.T(ax, 4.5, 10.6, r"$g(x)<0\ \Leftrightarrow\ x\in\!\left(\frac{\pi}{12},\frac{5\pi}{12}\right)$", lt, 2.6, 19, A.WHITE, ha="center")
    A.T(ax, 4.5, 9.6, r"$x_1+x_3>\frac{\pi}{2},\quad x_2>\frac{\pi}{4}$", lt, 3.5, 19, A.MUTED, ha="center")
    A.boxed(ax, 4.5, 8.3, r"$x_1+x_2+x_3>\frac{\pi}{2}+\frac{\pi}{4}=\frac{3\pi}{4}$", lt, 4.4, 19, A.GREEN)
    gax = fig.add_axes([0.12, 0.045, 0.78, 0.33])
    graph_part3(gax, lt)

def s_summary(fig, ax, lt, dur):
    A.T(ax, 4.5, 14.0, "结论", lt, 0.0, 30, A.WHITE, ha="center", weight="bold")
    rows = [
        ("1", A.BLUE,  r"$y=4\,\mathrm{e}^{\frac{\pi}{2}}\!\left(x-\frac{\pi}{2}\right)$"),
        ("2", A.GOLD,  r"$a\in\left(-\infty,-\mathrm{e}^{-\frac{\pi}{2}}\right]\cup\left[1,+\infty\right)$"),
        ("3", A.GREEN, r"$x_1+x_2+x_3>\frac{3\pi}{4}$"),
    ]
    y = 11.4
    for i, (idx, col, ans) in enumerate(rows):
        t0 = 0.5 + i * 0.9
        A.chip(ax, 1.1, y, idx, col, lt, t0)
        a = A.appear(lt, t0 + 0.15, 0.6)
        if a > 0.02:
            ax.text(5.0, y, ans, color=A.rgba(col, a), fontsize=21, ha="center", va="center",
                    weight="bold",
                    bbox=dict(boxstyle="round,pad=0.5", fc=A.rgba(col, 0.10 * a),
                              ec=A.rgba(col, 0.7 * a), lw=1.5))
        y -= 2.7

# ----------------------------------------------------------------------------- timeline
TIMELINE = [
    ("title",   s_title,   5.0),
    ("problem", s_problem, 11.0),
    ("part1",   s_part1,   16.0),
    ("part2",   s_part2,   16.0),
    ("part3",   s_part3,   17.0),
    ("summary", s_summary, 7.0),
]
TOTAL = sum(d for _, _, d in TIMELINE)
SCENE_COLOR = {"title": A.BLUE, "problem": A.WHITE, "part1": A.BLUE,
               "part2": A.GOLD, "part3": A.GREEN, "summary": A.WHITE}

def render_frame(fig, gt):
    fig.clf()
    fig.patch.set_facecolor(A.BG)
    ax = overlay(fig)
    acc = 0.0
    chosen = None
    for name, fn, d in TIMELINE:
        if gt < acc + d:
            chosen = (name, fn, d, acc)
            break
        acc += d
    if chosen is None:
        name, fn, d = TIMELINE[-1]
        chosen = (name, fn, d, TOTAL - d)
    name, fn, d, start = chosen
    lt = A.clamp(gt - start, 0, d)
    fn(fig, ax, lt, d)
    pbar(ax, gt, TOTAL, SCENE_COLOR.get(name, A.WHITE))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", type=float, default=None)
    ap.add_argument("--out", default="qa_v.png")
    ap.add_argument("--fps", type=int, default=FPS)
    args = ap.parse_args()
    fig = plt.figure(figsize=(W, H), dpi=DPI)
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
