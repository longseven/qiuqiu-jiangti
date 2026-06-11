# -*- coding: utf-8 -*-
"""
趣味·完整三问讲透版 (竖屏 9:16, ~2.7min) · 白板网格(paper)主题
三关:① 切线方程  ② 取值范围  ③ 不等式证明。把整道题的方法讲清楚 + 球球 + 晓伊配音。

复用 animate(A) / animate_fun(F) / animate_vertical(V) / mascot,导入后覆盖配色 = 浅色主题。

Usage:
  python animate_fun_full.py --at 60 --out qa.png
  python animate_fun_full.py --dpi 200          # 全部帧 -> frames_full/
"""
import argparse
import math
import os

import matplotlib.pyplot as plt
import numpy as np

import animate as A
import animate_fun as F
import animate_vertical as V
from mascot import draw_mascot

# ===== 套用「白板·网格」浅色主题(只在本进程生效,其它视频不受影响) =====
A.BG = "#f6f8fc"; A.WHITE = "#1f2a44"; A.MUTED = "#475569"; A.GRID = "#dbe3f0"
A.BLUE = "#2563eb"; A.GOLD = "#c2780c"; A.GREEN = "#0f8a3d"; A.PINK = "#ec5a86"
A.GPANEL = "#ffffff"; A.GSPINE = "#c4cfe0"
F.RED = "#e11d48"; F.HP = "#15a34a"; F.HPTRACK = "#eef2f8"
_CPAL = [A.GOLD, A.GREEN, A.BLUE, F.RED, "#a855f7", "#0891b2"]
for _i, _c in enumerate(F.CONFETTI):
    _c["col"] = _CPAL[_i % len(_CPAL)]

W, H, DPI = 10.8, 19.2, 100
FPS = 24
FRAMES_DIR = "frames_full"


def overlay(fig, dx=0.0, dy=0.0):
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(dx, 9 + dx); ax.set_ylim(dy, 16 + dy); ax.axis("off")
    for gx in np.arange(-0.6, 9.61, 0.6):       # 网格背景
        ax.plot([gx, gx], [-0.6, 16.6], color=A.GRID, lw=0.7, alpha=0.6, zorder=0)
    for gy in np.arange(-0.6, 16.61, 0.6):
        ax.plot([-0.6, 9.6], [gy, gy], color=A.GRID, lw=0.7, alpha=0.6, zorder=0)
    return ax


def _header(ax, lt, idx, title, color):
    F.tag(ax, 4.5, 14.25, f"关{idx} · {title}", color, lt, 0.1, 21)
    ax.plot([0.5, 8.5], [13.8, 13.8], color=A.GSPINE, lw=1.2, zorder=1)


def _gax(fig):
    return fig.add_axes([0.12, 0.05, 0.76, 0.30])     # 底部整幅图 (y≈0.8..5.6)


# ----------------------------------------------------------------------------- scenes
def s_hook(fig, ax, lt, dur):
    F.tag(ax, 4.5, 13.6, "导数压轴 · 三关挑战", F.RED, lt, 0.4, 21)
    F.PT(ax, 4.5, 11.9, "三连闯关!", lt, 0.2, 44, A.BLUE)
    A.T(ax, 4.5, 10.2, A.FUNC, lt, 1.2, 20, A.BLUE, ha="center", dur=0.4)
    A.T(ax, 4.5, 8.7, "① 切线   ② 取值范围   ③ 不等式", lt, 2.0, 18, A.MUTED, ha="center", dur=0.4)
    draw_mascot(ax, 4.5, 4.9, 1.05, "cheer" if lt > 2.6 else "happy", lt)


def s_part1(fig, ax, lt, dur):
    _header(ax, lt, "①", "切线方程", A.BLUE)
    A.T(ax, 4.5, 13.0, r"$a=\mathrm{e}^{-\pi}:\ f(x)=\mathrm{e}^{x}\cos 3x-\mathrm{e}^{-\pi}\mathrm{e}^{3x}\cos x$",
        lt, 1.0, 15, A.WHITE, ha="center", dur=0.4)
    A.T(ax, 4.5, 11.9, r"$f'(x)=\mathrm{e}^{x}(\cos 3x-3\sin 3x)$", lt, 5.0, 17, A.MUTED, ha="center", dur=0.4)
    A.T(ax, 4.5, 11.1, r"$\qquad-\,\mathrm{e}^{-\pi}\mathrm{e}^{3x}(3\cos x-\sin x)$", lt, 7.5, 17, A.MUTED, ha="center", dur=0.4)
    A.T(ax, 4.5, 9.9, r"$f\!\left(\frac{\pi}{2}\right)=0,\quad f'\!\left(\frac{\pi}{2}\right)=4\,\mathrm{e}^{\frac{\pi}{2}}$",
        lt, 13.0, 18, A.BLUE, ha="center", dur=0.4)
    A.boxed(ax, 4.5, 8.4, r"$y=4\,\mathrm{e}^{\frac{\pi}{2}}\!\left(x-\frac{\pi}{2}\right)$", lt, 19.0, 21, A.GOLD)
    F.score_pop(ax, 7.0, 8.6, lt, 19.5, color=A.GOLD)
    V.graph_part1(_gax(fig), lt)
    draw_mascot(ax, 1.35, 6.85, 0.55, "happy" if lt > 19 else "think", lt)


def s_part2(fig, ax, lt, dur):
    _header(ax, lt, "②", "取值范围", A.GOLD)
    A.T(ax, 4.5, 13.0, r"$f(x)=0\ \Rightarrow\ \mathrm{e}^{x}\cos 3x=a\,\mathrm{e}^{3x}\cos x$", lt, 1.0, 16, A.WHITE, ha="center", dur=0.4)
    A.T(ax, 4.5, 12.1, r"$\cos 3x=\cos x\,(2\cos 2x-1)$", lt, 5.0, 16, A.MUTED, ha="center", dur=0.4)
    A.T(ax, 4.5, 11.3, r"$\Rightarrow\ \dfrac{2\cos 2x-1}{\mathrm{e}^{2x}}=a$", lt, 7.5, 16, A.MUTED, ha="center", dur=0.4)
    A.T(ax, 4.5, 10.3, r"$t=2x:\ h(t)=\dfrac{2\cos t-1}{\mathrm{e}^{t}}\ \,$ 递减", lt, 11.0, 16, A.WHITE, ha="center", dur=0.4)
    A.T(ax, 4.5, 9.3, r"$h(0)=1,\quad h\!\left(\frac{\pi}{2}\right)=-\mathrm{e}^{-\frac{\pi}{2}}$", lt, 15.0, 16, A.WHITE, ha="center", dur=0.4)
    A.boxed(ax, 4.5, 7.9, r"$a\in\left(-\infty,-\mathrm{e}^{-\frac{\pi}{2}}\right]\cup\left[1,+\infty\right)$", lt, 21.0, 19, A.GOLD)
    F.score_pop(ax, 7.0, 8.1, lt, 21.5, color=A.GOLD)
    V.graph_part2(_gax(fig), lt)
    draw_mascot(ax, 1.35, 6.7, 0.55, "cool" if lt > 11 else "think", lt)


def s_part3(fig, ax, lt, dur):
    _header(ax, lt, "③", "不等式证明", A.GREEN)
    A.T(ax, 4.5, 13.0, r"$a=0:\ g(x)=2f(x)+f'(x)=3\sqrt{2}\,\mathrm{e}^{x}\cos\!\left(3x+\frac{\pi}{4}\right)$",
        lt, 1.0, 15, A.GREEN, ha="center", dur=0.4)
    A.T(ax, 4.5, 11.9, r"$g(x)<0\ \Leftrightarrow\ x\in\!\left(\frac{\pi}{12},\frac{5\pi}{12}\right)$", lt, 6.0, 17, A.WHITE, ha="center", dur=0.4)
    A.T(ax, 4.5, 10.9, r"$x_1+x_3>\frac{\pi}{2}$   (图象右偏)", lt, 12.0, 17, A.MUTED, ha="center", dur=0.4)
    A.T(ax, 4.5, 10.0, r"$x_2>\frac{\pi}{4}$   ($g'(x_2)=g(x_1)<0$)", lt, 18.0, 17, A.MUTED, ha="center", dur=0.4)
    A.boxed(ax, 4.5, 8.5, r"$x_1+x_2+x_3>\frac{\pi}{2}+\frac{\pi}{4}=\frac{3\pi}{4}$", lt, 24.0, 18, A.GREEN)
    F.score_pop(ax, 7.0, 8.7, lt, 24.5, color=A.GREEN)
    F.big_graph(_gax(fig), lt)
    draw_mascot(ax, 1.35, 6.85, 0.55, "love" if 6 < lt < 24 else ("cheer" if lt >= 24 else "think"), lt)


def s_summary(fig, ax, lt, dur):
    fl = A.clamp(1 - lt / 0.5)
    if fl > 0.01:
        ax.add_patch(plt.Rectangle((0, 0), 9, 16, color=A.rgba("#ffffff", 0.55 * fl), zorder=10))
    F.confetti(ax, lt, 0.1)
    F.PT(ax, 4.5, 13.6, "三关 · 通关!", lt, 0.2, 40, A.GOLD)
    rows = [("①", A.BLUE,  r"$y=4\,\mathrm{e}^{\frac{\pi}{2}}\!\left(x-\frac{\pi}{2}\right)$"),
            ("②", A.GOLD,  r"$a\in\left(-\infty,-\mathrm{e}^{-\frac{\pi}{2}}\right]\cup\left[1,+\infty\right)$"),
            ("③", A.GREEN, r"$x_1+x_2+x_3>\frac{3\pi}{4}$")]
    y = 11.2
    for i, (idx, col, ans) in enumerate(rows):
        t0 = 0.6 + i * 0.7
        A.chip(ax, 1.2, y, idx, col, lt, t0)
        a = A.appear(lt, t0 + 0.15, 0.5)
        if a > 0.02:
            ax.text(5.0, y, ans, color=A.rgba(col, a), fontsize=19, ha="center", va="center",
                    weight="bold", zorder=8,
                    bbox=dict(boxstyle="round,pad=0.4", fc=A.rgba(col, 0.1 * a),
                              ec=A.rgba(col, 0.7 * a), lw=1.4))
        y -= 1.7
    A.T(ax, 4.5, 4.6, "完整解析 · 关注主页 · 点赞收藏", lt, 3.0, 18, A.MUTED, ha="center", dur=0.4)
    draw_mascot(ax, 4.5, 2.1, 0.95, "thumbsup" if lt > 2.5 else "cheer", lt)


# ----------------------------------------------------------------------------- timeline
TIMELINE = [
    ("hook",    s_hook,    8.0),
    ("part1",   s_part1,   38.0),
    ("part2",   s_part2,   46.0),
    ("part3",   s_part3,   50.0),
    ("summary", s_summary, 14.0),
]
TOTAL = sum(d for _, _, d in TIMELINE)   # 156s

def progress_frac(gt):
    pts = [(0, 0.0), (8, 0.05), (46, 0.33), (92, 0.62), (142, 0.96), (TOTAL, 1.0)]
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
        dx, dy = F.shake(lt, 0.2, 0.5, 0.12)
    elif name == "summary":
        dx, dy = F.shake(lt, 0.15, 0.5, 0.14)
    ax = overlay(fig, dx, dy)
    fn(fig, ax, lt, d)
    F.hp_bar(ax, progress_frac(gt), lt if name == "hook" else 1.0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", type=float, default=None)
    ap.add_argument("--out", default="qff.png")
    ap.add_argument("--fps", type=int, default=FPS)
    ap.add_argument("--dpi", type=int, default=DPI)
    args = ap.parse_args()
    fig = plt.figure(figsize=(W, H), dpi=args.dpi)
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
        if i % 100 == 0:
            print(f"  frame {i}/{n}")
    print("done frames")

if __name__ == "__main__":
    main()
