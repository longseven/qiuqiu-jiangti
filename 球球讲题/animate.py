# -*- coding: utf-8 -*-
"""
导数压轴题 动画讲解
f(x) = e^x cos3x - a e^{3x} cos x
  (1) 切线方程   (2) 零点与取值范围   (3) 不等式证明

Usage:
  python animate.py --at 20 --out qa.png     # render a single frame at t=20s for QA
  python animate.py                          # render all frames -> out.mp4 + out.gif
"""
import argparse
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from matplotlib import font_manager

# ----------------------------------------------------------------------------- config
W, H, DPI = 12.8, 7.2, 100          # 1280 x 720
FPS = 24
FRAMES_DIR = "frames"

CJK = ["Microsoft YaHei", "SimHei", "SimSun"]
_avail = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams["font.sans-serif"] = [c for c in CJK if c in _avail] + ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["mathtext.fontset"] = "cm"

# palette (dark navy theme)
BG      = "#0f1226"
PANEL   = "#1a1f44"
WHITE   = "#f4f6ff"
MUTED   = "#9aa3c8"
BLUE    = "#6cc6ff"   # function / main
GOLD    = "#ffcf6e"   # results / answers
GREEN   = "#86efac"   # part 3 / g(x)
PINK    = "#ff95a8"   # inequalities
GRID    = "#2a2f57"
GPANEL  = "#12173a"   # graph 面板底色(浅色主题可覆盖)
GSPINE  = "#3a4070"   # graph 坐标轴线(浅色主题可覆盖)
ACCENTS = {"part1": BLUE, "part2": GOLD, "part3": GREEN}

# ----------------------------------------------------------------------------- helpers
def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

def ease(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)            # smoothstep

def appear(lt, t0, dur=0.55):
    """alpha 0->1 starting at t0."""
    return ease((lt - t0) / dur)

def rgba(color, a):
    r, g, b = mcolors.to_rgb(color)
    return (r, g, b, clamp(a))

def overlay_axes(fig):
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")
    return ax

def T(ax, x, y, s, lt, t0, size, color=WHITE, ha="left", weight="normal",
      dur=0.55, dy=0.32, family=None):
    """Fade + rise-in text."""
    a = appear(lt, t0, dur)
    if a <= 0.003:
        return
    yy = y - dy * (1 - ease((lt - t0) / dur))
    kw = {}
    if family:
        kw["fontfamily"] = family
    ax.text(x, yy, s, color=rgba(color, a), fontsize=size, ha=ha, va="center",
            weight=weight, **kw)

def boxed(ax, x, y, s, lt, t0, size, color=GOLD, ha="center", dur=0.6):
    """Answer text inside a soft rounded box; pops + fades in."""
    a = appear(lt, t0, dur)
    if a <= 0.003:
        return
    pop = 0.94 + 0.06 * ease((lt - t0) / dur)
    ax.text(x, y, s, color=rgba(color, a), fontsize=size * pop, ha=ha, va="center",
            weight="bold",
            bbox=dict(boxstyle="round,pad=0.55", fc=rgba(color, 0.12 * a),
                      ec=rgba(color, 0.85 * a), lw=1.6))

def chip(ax, x, y, label, color, lt, t0):
    """Small section chip e.g. (1)."""
    a = appear(lt, t0, 0.5)
    if a <= 0.003:
        return
    ax.text(x, y, label, color=rgba(BG, a), fontsize=17, ha="center", va="center",
            weight="bold",
            bbox=dict(boxstyle="circle,pad=0.34", fc=rgba(color, a), ec="none"))

def style_graph(gax, title=None, tcolor=WHITE):
    gax.set_facecolor(GPANEL)
    for sp in ("top", "right"):
        gax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        gax.spines[sp].set_color(GSPINE)
    gax.tick_params(colors=MUTED, labelsize=8, length=3)
    gax.grid(True, color=GRID, lw=0.6, alpha=0.5)
    if title:
        gax.set_title(title, color=tcolor, fontsize=12, pad=6)

def progress_bar(ax, gt, total, scene_color):
    p = clamp(gt / total)
    ax.add_patch(plt.Rectangle((0.6, 0.28), 14.8, 0.06, color=GRID, zorder=1))
    ax.add_patch(plt.Rectangle((0.6, 0.28), 14.8 * p, 0.06, color=scene_color, zorder=2))

# ----------------------------------------------------------------------------- math
A1 = math.exp(-math.pi)          # part 1: a = e^{-pi}
def f1(x):                       # part 1 function
    return np.exp(x) * np.cos(3 * x) - A1 * np.exp(3 * x) * np.cos(x)
def tangent1(x):
    s = 4 * math.exp(math.pi / 2)
    return s * (x - math.pi / 2)

def h2(t):                       # part 2: h(t) = (2cos t - 1)/e^t
    return (2 * np.cos(t) - 1) / np.exp(t)

def g3(x):                       # part 3: g(x) = 3 sqrt2 e^x cos(3x + pi/4)
    return 3 * math.sqrt(2) * np.exp(x) * np.cos(3 * x + math.pi / 4)
def g3p(x):                      # g'(x)
    c = 3 * math.sqrt(2)
    return c * np.exp(x) * (np.cos(3 * x + math.pi / 4) - 3 * np.sin(3 * x + math.pi / 4))

# pick faithful illustrative points for part 3: g(x1)=g(x3)=g'(x2)=L<0, x1<x2<x3
def part3_points():
    xs = np.linspace(0.30, 1.28, 4000)
    gv = g3(xs)
    gpv = g3p(xs)
    best = None
    for L in np.linspace(-9.0, -2.0, 400):
        # g == L crossings
        roots_g = xs[:-1][(gv[:-1] - L) * (gv[1:] - L) < 0]
        roots_gp = xs[:-1][(gpv[:-1] - L) * (gpv[1:] - L) < 0]
        if len(roots_g) >= 2 and len(roots_gp) >= 1:
            x1, x3 = roots_g[0], roots_g[-1]
            for x2 in roots_gp:
                if x1 < x2 < x3:
                    margin = min(x2 - x1, x3 - x2)
                    if best is None or margin > best[0]:
                        best = (margin, x1, x2, x3, L)
    if best:
        _, x1, x2, x3, L = best
        return x1, x2, x3, L
    return 0.45, 0.78, 1.15, g3(0.78)   # fallback

P3 = part3_points()

# ----------------------------------------------------------------------------- scenes
FUNC = r"$f(x)=\mathrm{e}^{x}\cos 3x-a\,\mathrm{e}^{3x}\cos x$"

def scene_title(fig, ax, lt, dur):
    # decorative curve drawing in the background
    p = ease(clamp(lt / 2.2))
    xs = np.linspace(0, math.pi / 2, 400)
    n = max(2, int(len(xs) * p))
    gax = fig.add_axes([0.08, 0.10, 0.84, 0.40])
    gax.axis("off")
    gax.set_xlim(0, math.pi / 2)
    gax.set_ylim(-3.4, 3.4)
    ys = np.exp(xs) * np.cos(3 * xs)
    gax.plot(xs[:n], ys[:n], color=rgba(BLUE, 0.35), lw=2.2)
    T(ax, 8.0, 6.6, "导数压轴题 · 动画精讲", lt, 0.2, 36, WHITE, ha="center", weight="bold")
    T(ax, 8.0, 5.3, FUNC, lt, 0.9, 27, BLUE, ha="center")
    T(ax, 8.0, 4.25, "切线  ·  零点  ·  不等式", lt, 1.6, 19, MUTED, ha="center")

def scene_problem(fig, ax, lt, dur):
    T(ax, 1.0, 8.25, "题目", lt, 0.0, 22, WHITE, weight="bold")
    ax.plot([1.0, 15.0], [7.8, 7.8], color=GRID, lw=1.2)
    T(ax, 8.0, 7.15, FUNC, lt, 0.3, 24, BLUE, ha="center")
    # three sub-questions
    chip(ax, 1.25, 5.85, "1", BLUE, lt, 1.4)
    T(ax, 2.0, 5.85, r"当 $a=\mathrm{e}^{-\pi}$ 时,求 $f(x)$ 在点 $\left(\frac{\pi}{2},f(\frac{\pi}{2})\right)$ 处的切线方程",
      lt, 1.5, 18, WHITE)
    chip(ax, 1.25, 4.35, "2", GOLD, lt, 3.0)
    T(ax, 2.0, 4.35, r"若 $f(x)$ 在 $\left(0,\frac{\pi}{4}\right)$ 上没有零点,求实数 $a$ 的取值范围",
      lt, 3.1, 18, WHITE)
    chip(ax, 1.25, 2.7, "3", GREEN, lt, 4.6)
    T(ax, 2.0, 3.0, r"当 $a=0$ 时,$g(x)=2f(x)+f'(x)$,若 $x_1<x_2<x_3\in\left(0,\frac{\pi}{2}\right)$",
      lt, 4.7, 18, WHITE)
    T(ax, 2.0, 2.35, r"满足 $g(x_1)=g'(x_2)=g(x_3)<0$,证明 $x_1+x_2+x_3>\frac{3\pi}{4}$",
      lt, 5.3, 18, WHITE)

def _header(ax, lt, idx, title, color):
    chip(ax, 1.2, 8.25, idx, color, lt, 0.0)
    T(ax, 1.9, 8.25, title, lt, 0.1, 22, color, weight="bold")
    ax.plot([1.0, 15.0], [7.75, 7.75], color=GRID, lw=1.2)

def scene_part1(fig, ax, lt, dur):
    _header(ax, lt, "1", "切线方程", BLUE)
    x0 = 0.9
    T(ax, x0, 7.0, r"$a=\mathrm{e}^{-\pi}:\ f(x)=\mathrm{e}^{x}\cos 3x-\mathrm{e}^{-\pi}\mathrm{e}^{3x}\cos x$",
      lt, 0.5, 18, WHITE)
    T(ax, x0, 6.1, r"$f'(x)=\mathrm{e}^{x}(\cos 3x-3\sin 3x)$", lt, 1.6, 18, MUTED)
    T(ax, x0, 5.45, r"$\qquad-\,\mathrm{e}^{-\pi}\mathrm{e}^{3x}(3\cos x-\sin x)$", lt, 2.2, 18, MUTED)
    T(ax, x0, 4.5, r"$f\!\left(\frac{\pi}{2}\right)=0$", lt, 3.2, 20, WHITE)
    T(ax, x0 + 2.8, 4.5, r"$f'\!\left(\frac{\pi}{2}\right)=4\,\mathrm{e}^{\frac{\pi}{2}}$", lt, 3.8, 20, BLUE)
    boxed(ax, 4.1, 3.1, r"$y=4\,\mathrm{e}^{\frac{\pi}{2}}\!\left(x-\frac{\pi}{2}\right)$", lt, 4.7, 22, GOLD)
    # graph: curve + tangent at pi/2
    gax = fig.add_axes([0.56, 0.16, 0.40, 0.60])
    style_graph(gax, r"$f(x)$ 与切线 @ $x=\frac{\pi}{2}$", BLUE)
    xs = np.linspace(1.15, 1.85, 400)
    pc = ease(clamp((lt - 1.0) / 1.8))
    nc = max(2, int(len(xs) * pc))
    gax.plot(xs[:nc], f1(xs[:nc]), color=BLUE, lw=2.4, label=r"$f(x)$")
    pt = ease(clamp((lt - 4.0) / 1.6))
    half = 0.34 * pt
    xtan = np.linspace(math.pi / 2 - half, math.pi / 2 + half, 50)
    gax.plot(xtan, tangent1(xtan), color=GOLD, lw=2.2, ls="--")
    if appear(lt, 3.0) > 0.2:
        gax.plot([math.pi / 2], [0], "o", color=PINK, ms=8, zorder=5)
        gax.annotate(r"$\left(\frac{\pi}{2},0\right)$", (math.pi / 2, 0),
                     textcoords="offset points", xytext=(8, -16), color=PINK, fontsize=11)
    gax.set_xlim(1.15, 1.85)
    gax.set_ylim(-5, 8)

def scene_part2(fig, ax, lt, dur):
    _header(ax, lt, "2", "零点与取值范围", GOLD)
    x0 = 0.9
    T(ax, x0, 7.0, r"$f(x)=0\ \Rightarrow\ \mathrm{e}^{x}\cos 3x=a\,\mathrm{e}^{3x}\cos x$", lt, 0.4, 18, WHITE)
    T(ax, x0, 6.15, r"$\cos 3x=\cos x\,(2\cos 2x-1)\ \Rightarrow\ \dfrac{2\cos 2x-1}{\mathrm{e}^{2x}}=a$",
      lt, 1.4, 18, MUTED)
    T(ax, x0, 5.2, r"令 $t=2x\in\!\left(0,\frac{\pi}{2}\right):\ h(t)=\dfrac{2\cos t-1}{\mathrm{e}^{t}}$",
      lt, 2.4, 18, WHITE)
    T(ax, x0, 4.25, r"$h'(t)=\dfrac{1-2\sqrt{2}\,\sin\!\left(t+\frac{\pi}{4}\right)}{\mathrm{e}^{t}}<0$  (递减)",
      lt, 3.3, 18, MUTED)
    T(ax, x0, 3.45, r"$h(0)=1,\quad h\!\left(\frac{\pi}{2}\right)=-\mathrm{e}^{-\frac{\pi}{2}}$",
      lt, 4.2, 18, WHITE)
    boxed(ax, 4.0, 2.1, r"$a\in\left(-\infty,-\mathrm{e}^{-\frac{\pi}{2}}\right]\cup\left[1,+\infty\right)$",
          lt, 5.1, 20, GOLD)
    # graph of h(t)
    gax = fig.add_axes([0.56, 0.16, 0.40, 0.60])
    style_graph(gax, r"$h(t)=\frac{2\cos t-1}{\mathrm{e}^{t}}$", GOLD)
    ts = np.linspace(0, math.pi / 2, 400)
    pc = ease(clamp((lt - 2.6) / 1.8))
    nc = max(2, int(len(ts) * pc))
    gax.plot(ts[:nc], h2(ts[:nc]), color=GOLD, lw=2.6)
    top, bot = 1.0, -math.exp(-math.pi / 2)
    ba = appear(lt, 4.4)
    if ba > 0.2:
        gax.axhspan(bot, top, color=rgba(GOLD, 0.10 * ba))
        gax.axhline(top, color=rgba(GREEN, 0.8 * ba), lw=1.2, ls=":")
        gax.axhline(bot, color=rgba(GREEN, 0.8 * ba), lw=1.2, ls=":")
        gax.plot([0], [top], "o", mfc="#12173a", mec=GOLD, ms=7)
        gax.plot([math.pi / 2], [bot], "o", mfc="#12173a", mec=GOLD, ms=7)
        gax.annotate(r"$1$", (0, top), xytext=(6, 4), textcoords="offset points",
                     color=GREEN, fontsize=10)
        gax.annotate(r"$-\mathrm{e}^{-\frac{\pi}{2}}$", (math.pi / 2, bot),
                     xytext=(-44, -2), textcoords="offset points", color=GREEN, fontsize=10)
        gax.text(0.78, 0.42, "有解区间\n(应排除)", color=rgba(MUTED, ba), fontsize=9,
                 ha="center", va="center")
    gax.set_xlim(0, math.pi / 2)
    gax.set_ylim(-0.55, 1.2)

def scene_part3(fig, ax, lt, dur):
    _header(ax, lt, "3", r"证明  $x_1+x_2+x_3>\frac{3\pi}{4}$", GREEN)
    x0 = 0.9
    T(ax, x0, 7.0, r"$a=0:\ f(x)=\mathrm{e}^{x}\cos 3x$", lt, 0.4, 18, WHITE)
    T(ax, x0, 6.1, r"$g(x)=2f(x)+f'(x)=3\sqrt{2}\,\mathrm{e}^{x}\cos\!\left(3x+\frac{\pi}{4}\right)$",
      lt, 1.3, 18, GREEN)
    T(ax, x0, 5.15, r"$g(x)<0\ \Leftrightarrow\ x\in\!\left(\frac{\pi}{12},\frac{5\pi}{12}\right)$",
      lt, 2.4, 18, WHITE)
    T(ax, x0, 4.3, r"$x_1+x_3>\dfrac{\pi}{2}$  (图象右偏)", lt, 3.4, 18, MUTED)
    T(ax, x0, 3.6, r"$x_2>\dfrac{\pi}{4}$", lt, 4.2, 18, MUTED)
    boxed(ax, 3.4, 2.2, r"$x_1+x_2+x_3>\dfrac{\pi}{2}+\dfrac{\pi}{4}=\dfrac{3\pi}{4}$",
          lt, 5.1, 19, GREEN)
    # graph of g(x) with x1<x2<x3
    gax = fig.add_axes([0.56, 0.16, 0.40, 0.60])
    style_graph(gax, r"$g(x)=3\sqrt{2}\,\mathrm{e}^{x}\cos(3x+\frac{\pi}{4})$", GREEN)
    xs = np.linspace(0, 1.42, 500)
    pc = ease(clamp((lt - 1.5) / 1.8))
    nc = max(2, int(len(xs) * pc))
    gax.plot(xs[:nc], g3(xs[:nc]), color=GREEN, lw=2.4)
    gax.axhline(0, color="#4a5080", lw=1.0)
    z1, z2 = math.pi / 12, 5 * math.pi / 12
    ba = appear(lt, 3.0)
    if ba > 0.2:
        gax.axvspan(z1, z2, color=rgba(GREEN, 0.08 * ba))
        for z, lab in ((z1, r"$\frac{\pi}{12}$"), (z2, r"$\frac{5\pi}{12}$")):
            gax.axvline(z, color=rgba(MUTED, 0.7 * ba), lw=1.0, ls=":")
            gax.annotate(lab, (z, 0), xytext=(2, 8), textcoords="offset points",
                         color=rgba(MUTED, ba), fontsize=10)
    x1, x2, x3, L = P3
    pa = appear(lt, 4.2)
    if pa > 0.2:
        gax.axhline(L, color=rgba(PINK, 0.5 * pa), lw=1.0, ls="--")
        for xv, lab, col in ((x1, r"$x_1$", PINK), (x2, r"$x_2$", GOLD), (x3, r"$x_3$", PINK)):
            yv = g3(xv)
            gax.plot([xv], [yv], "o", color=rgba(col, pa), ms=8, zorder=6)
            gax.annotate(lab, (xv, yv), xytext=(-4, -16), textcoords="offset points",
                         color=rgba(col, pa), fontsize=11)
    gax.set_xlim(0, 1.42)
    gax.set_ylim(-10.5, 6)

def scene_summary(fig, ax, lt, dur):
    T(ax, 8.0, 8.0, "结论", lt, 0.0, 26, WHITE, ha="center", weight="bold")
    rows = [
        ("1", BLUE,  r"$y=4\,\mathrm{e}^{\frac{\pi}{2}}\!\left(x-\frac{\pi}{2}\right)$"),
        ("2", GOLD,  r"$a\in\left(-\infty,-\mathrm{e}^{-\frac{\pi}{2}}\right]\cup\left[1,+\infty\right)$"),
        ("3", GREEN, r"$x_1+x_2+x_3>\dfrac{3\pi}{4}$"),
    ]
    y = 6.2
    for i, (idx, col, ans) in enumerate(rows):
        t0 = 0.5 + i * 0.9
        chip(ax, 2.3, y, idx, col, lt, t0)
        a = appear(lt, t0 + 0.15, 0.6)
        if a > 0.02:
            ax.text(8.4, y, ans, color=rgba(col, a), fontsize=22, ha="center", va="center",
                    weight="bold",
                    bbox=dict(boxstyle="round,pad=0.5", fc=rgba(col, 0.10 * a),
                              ec=rgba(col, 0.7 * a), lw=1.4))
        y -= 1.8

# ----------------------------------------------------------------------------- timeline
TIMELINE = [
    ("title",   scene_title,   5.0),
    ("problem", scene_problem, 11.0),
    ("part1",   scene_part1,   16.0),
    ("part2",   scene_part2,   16.0),
    ("part3",   scene_part3,   17.0),
    ("summary", scene_summary, 7.0),
]
TOTAL = sum(d for _, _, d in TIMELINE)

SCENE_COLOR = {"title": BLUE, "problem": WHITE, "part1": BLUE,
               "part2": GOLD, "part3": GREEN, "summary": WHITE}

def render_frame(fig, gt):
    fig.clf()
    fig.patch.set_facecolor(BG)
    ax = overlay_axes(fig)
    acc = 0.0
    cur = TIMELINE[-1]
    for name, fn, d in TIMELINE:
        if gt < acc + d or name == TIMELINE[-1][0]:
            cur = (name, fn, d, acc)
            if gt < acc + d:
                break
        acc += d
    name, fn, d, start = cur
    lt = clamp(gt - start, 0, d)
    fn(fig, ax, lt, d)
    progress_bar(ax, gt, TOTAL, SCENE_COLOR.get(name, WHITE))

# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", type=float, default=None, help="render single frame at t seconds")
    ap.add_argument("--out", default="qa.png")
    ap.add_argument("--fps", type=int, default=FPS)
    args = ap.parse_args()

    fig = plt.figure(figsize=(W, H), dpi=DPI)
    if args.at is not None:
        render_frame(fig, args.at)
        fig.savefig(args.out, facecolor=BG)
        print("wrote", args.out, "at t=", args.at)
        return

    os.makedirs(FRAMES_DIR, exist_ok=True)
    n = int(TOTAL * args.fps)
    print(f"rendering {n} frames ({TOTAL}s @ {args.fps}fps)")
    for i in range(n):
        gt = i / args.fps
        render_frame(fig, gt)
        fig.savefig(os.path.join(FRAMES_DIR, f"f{i:05d}.png"), facecolor=BG)
        if i % 50 == 0:
            print(f"  frame {i}/{n}")
    print("done frames")

if __name__ == "__main__":
    main()
