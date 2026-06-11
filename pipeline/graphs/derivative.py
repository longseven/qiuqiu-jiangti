# -*- coding: utf-8 -*-
"""导数题型图象插件(由 animate_vertical.graph_part1/2/3 + animate_fun.big_graph 重构)。

本模块自带本题的数学事实(f/g/h 及标注点),params 可覆盖子动画节拍。
插件清单见 PLUGINS;接口统一为 fn(gax, lt, dur, params)。
"""
import math

import numpy as np

from ..core import C, appear, clamp, ease, ease_back, rgba, style_graph

PLUGINS = ["tangent", "h_mono", "valley"]

# ----------------------------------------------------------------------------- 数学事实
A1 = math.exp(-math.pi)                  # 第(1)问 a = e^{-pi}


def f1(x):
    return np.exp(x) * np.cos(3 * x) - A1 * np.exp(3 * x) * np.cos(x)


def tangent1(x):
    s = 4 * math.exp(math.pi / 2)
    return s * (x - math.pi / 2)


def h2(t):                               # 第(2)问 h(t) = (2cos t - 1)/e^t
    return (2 * np.cos(t) - 1) / np.exp(t)


def g3(x):                               # 第(3)问 g(x) = 3√2 e^x cos(3x+π/4)
    return 3 * math.sqrt(2) * np.exp(x) * np.cos(3 * x + math.pi / 4)


def g3p(x):
    c = 3 * math.sqrt(2)
    return c * np.exp(x) * (np.cos(3 * x + math.pi / 4) - 3 * np.sin(3 * x + math.pi / 4))


def _part3_points():
    """取一组忠实的示意点:g(x1)=g(x3)=g'(x2)=L<0 且 x1<x2<x3。"""
    xs = np.linspace(0.30, 1.28, 4000)
    gv = g3(xs)
    gpv = g3p(xs)
    best = None
    for L in np.linspace(-9.0, -2.0, 400):
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
    return 0.45, 0.78, 1.15, g3(0.78)    # fallback


P3 = _part3_points()


# ----------------------------------------------------------------------------- 插件
def tangent(gax, lt, dur, params):
    """f(x) 曲线 + x=π/2 处切线与切点。"""
    p = params or {}
    style_graph(gax, p.get("title", r"$f(x)$ 与切线 @ $x=\frac{\pi}{2}$"), C.BLUE)
    t_curve = p.get("t_curve", 1.0)      # 曲线开始绘制
    t_point = p.get("t_point", 3.0)      # 切点标注
    t_tan = p.get("t_tan", 4.0)          # 切线展开
    xs = np.linspace(1.15, 1.85, 400)
    pc = ease(clamp((lt - t_curve) / 1.8))
    nc = max(2, int(len(xs) * pc))
    gax.plot(xs[:nc], f1(xs[:nc]), color=C.BLUE, lw=2.6)
    pt = ease(clamp((lt - t_tan) / 1.6))
    half = 0.34 * pt
    xt = np.linspace(math.pi / 2 - half, math.pi / 2 + half, 50)
    gax.plot(xt, tangent1(xt), color=C.GOLD, lw=2.4, ls="--")
    if appear(lt, t_point) > 0.2:
        gax.plot([math.pi / 2], [0], "o", color=C.PINK, ms=9, zorder=5)
        gax.annotate(r"$\left(\frac{\pi}{2},0\right)$", (math.pi / 2, 0),
                     textcoords="offset points", xytext=(8, -18), color=C.PINK, fontsize=12)
    gax.set_xlim(1.15, 1.85)
    gax.set_ylim(-5, 8)


def h_mono(gax, lt, dur, params):
    """h(t) 单调递减曲线 + 值域水平带。"""
    p = params or {}
    style_graph(gax, p.get("title", r"$h(t)=\frac{2\cos t-1}{\mathrm{e}^{t}}$"), C.GOLD)
    t_curve = p.get("t_curve", 2.6)
    t_band = p.get("t_band", 4.4)
    ts = np.linspace(0, math.pi / 2, 400)
    pc = ease(clamp((lt - t_curve) / 1.8))
    nc = max(2, int(len(ts) * pc))
    gax.plot(ts[:nc], h2(ts[:nc]), color=C.GOLD, lw=2.8)
    top, bot = 1.0, -math.exp(-math.pi / 2)
    ba = appear(lt, t_band)
    if ba > 0.2:
        gax.axhspan(bot, top, color=rgba(C.GOLD, 0.10 * ba))
        gax.axhline(top, color=rgba(C.GREEN, 0.8 * ba), lw=1.3, ls=":")
        gax.axhline(bot, color=rgba(C.GREEN, 0.8 * ba), lw=1.3, ls=":")
        gax.plot([0], [top], "o", mfc=C.GPANEL, mec=C.GOLD, ms=7)
        gax.plot([math.pi / 2], [bot], "o", mfc=C.GPANEL, mec=C.GOLD, ms=7)
        gax.annotate(r"$1$", (0, top), xytext=(6, 5), textcoords="offset points",
                     color=C.GREEN, fontsize=11)
        gax.annotate(r"$-\mathrm{e}^{-\frac{\pi}{2}}$", (math.pi / 2, bot),
                     xytext=(-60, 16), textcoords="offset points", color=C.GREEN, fontsize=12)
        gax.text(0.78, 0.42, "有解区间(应排除)", color=rgba(C.MUTED, ba), fontsize=10,
                 ha="center", va="center")
    gax.set_xlim(0, math.pi / 2)
    gax.set_ylim(-0.55, 1.2)


# ---- 山谷图的小球(从 animate_fun.ball_x/draw_ball 重构,节拍可调) ----
def _ball_x(lt, t_roll, roll_dur=4.0):
    p = clamp((lt - t_roll) / roll_dur)
    xe = ease(p)
    x = 0.02 + (0.89 - 0.02) * xe
    t_settle = t_roll + roll_dur
    if lt > t_settle:
        x = 0.89 + 0.05 * math.sin((lt - t_settle) * 2.0) * math.exp(-(lt - t_settle) * 0.6)
    return x


def _draw_ball(gax, lt, t_roll):
    if lt < t_roll - 0.1:
        return
    bx = _ball_x(lt, t_roll)
    by = g3(bx)
    for k in range(1, 6):                                  # 拖尾
        tx = _ball_x(lt - 0.06 * k, t_roll)
        gax.scatter([tx], [g3(tx)], s=520 - 70 * k, color=rgba(C.GREEN, 0.10),
                    zorder=4, linewidths=0)
    for sz, al in ((2600, 0.10), (1500, 0.18), (820, 0.34)):   # 光晕
        gax.scatter([bx], [by], s=sz, color=rgba(C.GREEN, al), zorder=5, linewidths=0)
    gax.scatter([bx], [by], s=360, color="#d8fff0", edgecolors=C.GREEN, linewidths=2, zorder=6)


def valley(gax, lt, dur, params):
    """g(x) 山谷图:负值区间带 + 小球滚入 + x1/x2/x3 标注(full2 第三关主图)。"""
    p = params or {}
    style_graph(gax, p.get("title"))
    t_curve = p.get("t_curve", 0.3)
    t_roll = p.get("t_roll", 1.5)        # 小球滚入
    t_band = p.get("t_band", 5.6)        # 负值区间
    t_pts = p.get("t_pts", 6.5)          # x1/x3
    t_x2 = p.get("t_x2", 9.0)            # x2
    xs = np.linspace(0, 1.42, 500)
    pc = ease(clamp((lt - t_curve) / 1.4))
    nc = max(2, int(len(xs) * pc))
    gax.plot(xs[:nc], g3(xs[:nc]), color=C.GREEN, lw=3.2)
    gax.axhline(0, color=C.GSPINE, lw=1.0)
    z1, z2 = math.pi / 12, 5 * math.pi / 12
    ba = appear(lt, t_band)
    if ba > 0.2:
        gax.axvspan(z1, z2, color=rgba(C.GREEN, 0.10 * ba))
        for z, lab, dxo, hao in ((z1, r"$\frac{\pi}{12}$", 3, "left"),
                                 (z2, r"$\frac{5\pi}{12}$", -3, "right")):
            gax.axvline(z, color=rgba(C.MUTED, 0.7 * ba), lw=1.0, ls=":")
            gax.annotate(lab, (z, 0), xytext=(dxo, 10), textcoords="offset points",
                         color=rgba(C.MUTED, ba), fontsize=13, ha=hao)
    _draw_ball(gax, lt, t_roll)
    x1, x2, x3, L = P3
    if lt > t_pts:
        p13 = ease_back(clamp((lt - t_pts) / 0.5))
        gax.axhline(L, color=rgba(C.RED, 0.45), lw=1.2, ls="--")
        for xv, lab in ((x1, r"$x_1$"), (x3, r"$x_3$")):
            gax.scatter([xv], [g3(xv)], s=240 * p13, color=C.RED, zorder=7,
                        edgecolors="white", linewidths=1.5)
            gax.annotate(lab, (xv, g3(xv)), xytext=(-6, -26), textcoords="offset points",
                         color=C.RED, fontsize=15, weight="bold")
    if lt > t_x2:
        p2 = ease_back(clamp((lt - t_x2) / 0.5))
        gax.scatter([x2], [g3(x2)], s=240 * p2, color=C.GOLD, zorder=7,
                    edgecolors="white", linewidths=1.5)
        gax.annotate(r"$x_2$", (x2, g3(x2)), xytext=(-6, 16), textcoords="offset points",
                     color=C.GOLD, fontsize=15, weight="bold")
    gax.set_xlim(0, 1.42)
    gax.set_ylim(-10.5, 6)
    gax.tick_params(labelsize=10)
