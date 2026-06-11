# -*- coding: utf-8 -*-
"""
趣味·完整三问·闯关版 (竖屏 9:16, ~2.5min) · 空白背景(无网格) · 大字号
hook → [关①card→part→通关] → [关②...] → [关③...] → 全通关summary
游戏感:关卡转场卡 / 压轴BOSS血条(每关掉血+暴击震屏) / 球球当主角(放大+指公式+更皮台词)
       / 公式弹跳入场 + 答案星爆 +「漂亮!」/「连击!」/ BOSS击败KO。

复用 animate_fun_full(浅色主题) + animate_fun(UI) + animate_vertical(graphs) + mascot。
本版:去掉网格背景(纯空白浅底),整体字号加大,过长公式拆两行。

Usage:
  python animate_fun_full2.py --at 60 --out qa.png
  python animate_fun_full2.py --dpi 200          # 全部帧 -> frames_full2/
"""
import argparse
import math
import os

import matplotlib.pyplot as plt
import matplotlib.patches as mp
import numpy as np

import animate_fun_full as M
A, F, V, draw_mascot = M.A, M.F, M.V, M.draw_mascot

W, H = M.W, M.H
FRAMES_DIR = "frames_full2"


def overlay(fig, dx=0.0, dy=0.0):
    """纯空白背景(无网格)。"""
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(dx, 9 + dx); ax.set_ylim(dy, 16 + dy); ax.axis("off")
    return ax


def _gax(fig):
    return fig.add_axes([0.13, 0.045, 0.74, 0.255])   # 底部图,留位置给大字+球球


# ----------------------------------------------------------------------------- 趣味组件
def slide_in(lt, t0, dur=0.5):
    p = A.clamp((lt - t0) / dur)
    if p <= 0.0:
        return 0.0, 1.5
    return A.clamp(p / 0.4), 1.5 * (1 - F.ease_back(p))


def ST(ax, x, y, s, lt, t0, size, color, ha="center", weight="bold", dur=0.5, z=7):
    a, dx = slide_in(lt, t0, dur)
    if a <= 0.02:
        return
    ax.text(x + dx, y, s, color=A.rgba(color, a), fontsize=size, ha=ha, va="center",
            weight=weight, zorder=z)


def boxed_pop(ax, x, y, s, lt, t0, size, color):
    b = A.clamp((lt - t0) / 0.4)
    if b <= 0.02:
        return
    ax.text(x, y, s, color=A.rgba(color, b), fontsize=size * (0.6 + 0.4 * F.ease_back(b)),
            ha="center", va="center", weight="bold", zorder=8,
            bbox=dict(boxstyle="round,pad=0.55", fc=A.rgba(color, 0.12 * b),
                      ec=A.rgba(color, 0.9 * b), lw=2.2))


def pop(ax, x, y, text, lt, t0, color, size=28, rise=1.0, hold=1.2, bg=False, z=10):
    p = (lt - t0) / hold
    if p <= 0 or p >= 1:
        return
    a = min(1.0, p / 0.18) * (1 - p) ** 0.5
    sc = F.ease_back(min(1.0, p / 0.25))
    kw = {}
    if bg:
        kw["bbox"] = dict(boxstyle="round,pad=0.4", fc=A.rgba("#ffffff", 0.85 * a), ec="none")
    ax.text(x, y + rise * A.ease(A.clamp(p)), text, color=A.rgba(color, a),
            fontsize=size * (0.5 + 0.5 * sc), ha="center", va="center", weight="bold", zorder=z, **kw)


def starburst(ax, x, y, lt, t0, color, n=14, R=1.4):
    p = (lt - t0) / 0.75
    if p <= 0 or p >= 1:
        return
    a = (1 - p) ** 0.7
    e = A.ease(A.clamp(p))
    xs = [x + R * e * math.cos(k / n * 2 * math.pi) for k in range(n)]
    ys = [y + R * e * math.sin(k / n * 2 * math.pi) for k in range(n)]
    ax.scatter(xs, ys, s=210 * (1 - 0.5 * p), marker="*", color=A.rgba(color, a),
               zorder=9, linewidths=0)


def sparkles(ax, cx, cy, lt, t0, n=12):
    if lt < t0:
        return
    fade = A.clamp((lt - t0) / 0.4)
    for k in range(n):
        ang = k / n * 2 * math.pi + 0.4
        r = 2.6 + 0.8 * ((k * 7) % 5) / 5
        tw = 0.4 + 0.6 * abs(math.sin(lt * 3.4 + k))
        ax.scatter([cx + r * math.cos(ang)], [cy + r * 0.7 * math.sin(ang)], s=110, marker="*",
                   color=A.rgba(A.GOLD, 0.78 * tw * fade), zorder=6, linewidths=0)


def bubble(ax, x, y, text, lt, t0, color=None, hold=2.0):
    color = color or A.BLUE
    if not (t0 <= lt <= t0 + hold):
        return
    a = A.ease(A.clamp((lt - t0) / 0.28)) * A.clamp((t0 + hold - lt) / 0.3)
    if a <= 0.02:
        return
    ax.text(x, y, text, color=A.rgba("#ffffff", a), fontsize=20, ha="center", va="center",
            weight="bold", zorder=9,
            bbox=dict(boxstyle="round,pad=0.5", fc=A.rgba(color, a), ec="none"))
    ax.add_patch(mp.Polygon([[x - 0.3, y - 0.30], [x + 0.06, y - 0.30], [x - 0.5, y - 0.7]],
                 color=A.rgba(color, a), zorder=8))


# ---- 压轴 BOSS 血条 ----
CRITS = [41.0, 84.5, 134.0]

def boss_hp(gt):
    if gt < CRITS[0]:
        return 1.0
    if gt < CRITS[1]:
        return 1.0 - 0.33 * A.ease(A.clamp((gt - CRITS[0]) / 0.6))
    if gt < CRITS[2]:
        return 0.67 - 0.34 * A.ease(A.clamp((gt - CRITS[1]) / 0.6))
    return max(0.0, 0.33 - 0.33 * A.ease(A.clamp((gt - CRITS[2]) / 0.6)))


def boss_bar(ax, gt):
    hp = boss_hp(gt)
    ax.text(0.55, 15.33, "压轴BOSS", color=F.RED, fontsize=18, ha="left", va="center",
            weight="bold", zorder=8)
    x, y, w, h = 2.75, 15.1, 3.85, 0.46
    ax.add_patch(mp.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                 fc=F.HPTRACK, ec=A.GRID, lw=1.4, zorder=7))
    if hp > 0.001:
        ax.add_patch(mp.FancyBboxPatch((x + 0.07, y + 0.07), max(0.001, (w - 0.14) * hp), h - 0.14,
                     boxstyle="round,pad=0.03", fc=F.RED, ec="none", zorder=8))
    ax.text(x + w + 0.22, y + h / 2, "KO" if hp <= 0.001 else f"{int(round(hp*100))}%",
            color=F.RED, fontsize=18, ha="left", va="center", weight="bold", zorder=8)
    for ct in CRITS[:2]:
        if 0 <= gt - ct < 1.15:
            p = (gt - ct) / 1.15
            ax.text(4.5, 14.45 - 0.7 * A.ease(p), "暴击 -33%!", color=A.rgba(F.RED, 1 - p),
                    fontsize=32, ha="center", va="center", weight="bold", zorder=10)


# ----------------------------------------------------------------------------- 转场/通关
def card(ax, lt, idx, title, color):
    sparkles(ax, 4.5, 9.6, lt, 0.5, 13)
    ST(ax, 4.5, 10.7, f"关 {idx}", lt, 0.1, 72, color)
    ST(ax, 4.5, 8.9, title, lt, 0.35, 44, A.WHITE)
    pop(ax, 4.5, 7.1, "START!", lt, 0.7, color, size=48, rise=0.0, hold=1.8)
    draw_mascot(ax, 4.5, 3.9, 1.2, "cheer" if lt > 0.6 else "happy", lt)


def clear_scene(ax, lt, idx, color, xp, final=False):
    if final and lt < 0.4:
        ax.add_patch(plt.Rectangle((0, 0), 9, 16, color=A.rgba("#ffffff", 0.6 * (1 - lt / 0.4)),
                     zorder=11))
    F.confetti(ax, lt, 0.15)
    if final:
        F.confetti(ax, lt, 0.7)
    title = "BOSS 击败!" if final else f"关{idx} 通关!"
    ST(ax, 4.5, 10.6, title, lt, 0.1, 64 if final else 58, F.RED if final else color, z=12)
    pop(ax, 4.5, 8.6, f"+{xp} XP", lt, 0.6, A.GOLD, size=50, bg=True, z=12)
    if idx == "②":
        pop(ax, 4.5, 7.0, "连击 x2!", lt, 0.95, F.RED, size=36, bg=True, z=12)
    elif idx == "③":
        pop(ax, 4.5, 7.0, "连击 x3 · 完美!", lt, 0.95, F.RED, size=36, bg=True, z=12)
    draw_mascot(ax, 4.5, 3.9, 1.15, "thumbsup" if lt > 0.7 else "cheer", lt)


# ----------------------------------------------------------------------------- 关卡内容
def _part_common(ax, lt, idx, title, color):
    F.tag(ax, 4.5, 14.35, f"关{idx} · {title}", color, lt, 0.0, 30)


def s_hook(fig, ax, lt, dur):
    F.tag(ax, 4.5, 13.4, "导数压轴 · 三关挑战", F.RED, lt, 0.3, 28)
    F.PT(ax, 4.5, 11.6, "三连闯关!", lt, 0.15, 60, A.BLUE)
    A.T(ax, 4.5, 9.9, A.FUNC, lt, 1.1, 29, A.BLUE, ha="center", dur=0.4)
    A.T(ax, 4.5, 8.5, "① 切线   ② 取值范围   ③ 不等式", lt, 1.9, 26, A.MUTED, ha="center", dur=0.4)
    draw_mascot(ax, 4.5, 4.6, 1.1, "cheer" if lt > 2.4 else "happy", lt)
    bubble(ax, 6.5, 6.1, "三道压轴,我全包!", lt, 2.6, A.BLUE)


def _mascot_say(ax, lt, expr, lines):
    """球球(主角)在左侧 + 轮流冒泡。lines=[(t0,text,color),...]"""
    draw_mascot(ax, 1.5, 6.4, 0.68, expr, lt)
    for t0, text, col in lines:
        bubble(ax, 3.5, 6.95, text, lt, t0, col, hold=2.0)


def s_part1(fig, ax, lt, dur):
    _part_common(ax, lt, "①", "切线方程", A.BLUE)
    ST(ax, 4.5, 13.0, r"$a=\mathrm{e}^{-\pi}:\ f(x)=\mathrm{e}^{x}\cos 3x-\mathrm{e}^{-\pi}\mathrm{e}^{3x}\cos x$",
       lt, 1.0, 19, A.WHITE)
    ST(ax, 4.5, 11.85, r"$f'(x)=\mathrm{e}^{x}(\cos 3x-3\sin 3x)$", lt, 7.0, 24, A.MUTED)
    ST(ax, 4.5, 10.75, r"$\qquad-\,\mathrm{e}^{-\pi}\mathrm{e}^{3x}(3\cos x-\sin x)$", lt, 8.3, 24, A.MUTED)
    ST(ax, 4.5, 9.5, r"$f\!\left(\frac{\pi}{2}\right)=0,\quad f'\!\left(\frac{\pi}{2}\right)=4\,\mathrm{e}^{\frac{\pi}{2}}$",
       lt, 14.0, 30, A.BLUE)
    if lt > 22.0:
        boxed_pop(ax, 4.5, 8.0, r"$y=4\,\mathrm{e}^{\frac{\pi}{2}}\!\left(x-\frac{\pi}{2}\right)$", lt, 22.0, 34, A.GOLD)
        starburst(ax, 4.5, 8.0, lt, 22.2, A.GOLD)
        pop(ax, 7.5, 9.5, "漂亮!", lt, 22.4, A.PINK, size=30)
    V.graph_part1(_gax(fig), lt)
    expr = "point" if 1.5 < lt < 21.5 else ("happy" if lt >= 21.5 else "think")
    _mascot_say(ax, lt, expr, [(2.3, "求导,上!", A.BLUE), (9.0, "x=π/2 一代,直接归零!", A.GREEN),
                               (15.0, "斜率 4e^{π/2},稳~", A.BLUE), (22.4, "切线拿下!", A.GOLD)])


def s_part2(fig, ax, lt, dur):
    _part_common(ax, lt, "②", "取值范围", A.GOLD)
    ST(ax, 4.5, 13.0, r"$f(x)=0\ \Rightarrow\ \mathrm{e}^{x}\cos 3x=a\,\mathrm{e}^{3x}\cos x$", lt, 1.0, 20, A.WHITE)
    ST(ax, 4.5, 11.85, r"$\cos 3x=\cos x\,(2\cos 2x-1)$", lt, 8.0, 23, A.MUTED)
    ST(ax, 4.5, 10.7, r"$\Rightarrow\ \dfrac{2\cos 2x-1}{\mathrm{e}^{2x}}=a$", lt, 14.0, 23, A.MUTED)
    ST(ax, 4.5, 9.45, r"$t=2x:\ h(t)=\dfrac{2\cos t-1}{\mathrm{e}^{t}}\ \,$ 递减 (见图)", lt, 20.0, 22, A.WHITE)
    if lt > 33.0:
        boxed_pop(ax, 4.5, 8.05, r"$a\in\left(-\infty,-\mathrm{e}^{-\frac{\pi}{2}}\right]\cup\left[1,+\infty\right)$", lt, 33.0, 26, A.GOLD)
        starburst(ax, 4.5, 8.05, lt, 33.2, A.GOLD)
        pop(ax, 7.5, 8.7, "漂亮!", lt, 33.4, A.PINK, size=30)
    V.graph_part2(_gax(fig), lt)
    expr = "cool" if lt > 20 else "think"
    _mascot_say(ax, lt, expr, [(2.5, "f=0,移项!", A.GOLD), (8.5, "cos3x 拆开~", A.BLUE),
                               (14.5, "cosx 约掉,清爽!", A.GREEN), (20.5, "换元 t=2x", A.GOLD),
                               (27.5, "一路向下,递减!", A.BLUE), (33.4, "a 躲区间外去!", A.GOLD)])


def s_part3(fig, ax, lt, dur):
    _part_common(ax, lt, "③", "不等式证明", A.GREEN)
    ST(ax, 4.5, 13.0, r"$a=0:\ g(x)=2f(x)+f'(x)$", lt, 1.0, 23, A.GREEN)
    ST(ax, 4.5, 11.85, r"$\qquad=3\sqrt{2}\,\mathrm{e}^{x}\cos\!\left(3x+\frac{\pi}{4}\right)$", lt, 2.2, 23, A.GREEN)
    ST(ax, 4.5, 10.55, r"$g(x)<0\ \Leftrightarrow\ x\in\!\left(\frac{\pi}{12},\frac{5\pi}{12}\right)$", lt, 8.0, 24, A.WHITE)
    ST(ax, 4.5, 9.3, r"$x_1+x_3>\frac{\pi}{2}$,$\quad$ $x_2>\frac{\pi}{4}$", lt, 18.0, 23, A.MUTED)
    if lt > 37.0:
        boxed_pop(ax, 4.5, 7.95, r"$x_1+x_2+x_3>\frac{\pi}{2}+\frac{\pi}{4}=\frac{3\pi}{4}$", lt, 37.0, 27, A.GREEN)
        starburst(ax, 4.5, 7.95, lt, 37.2, A.GREEN)
        pop(ax, 7.5, 8.7, "得证!", lt, 37.4, A.PINK, size=30)
    F.big_graph(_gax(fig), lt)
    expr = "love" if 9 < lt < 37 else ("cheer" if lt >= 37 else "think")
    _mascot_say(ax, lt, expr, [(2.5, "g 登场!", A.GREEN), (4.2, "合体成 3√2 余弦,帅!", A.BLUE),
                               (9.0, "小球滚进山谷~", A.GREEN), (19.0, "e^x 偏心,右边更猛!", A.PINK),
                               (29.0, "x2 卡谷底,>π/4", A.GOLD), (37.4, "三个一加,超 3π/4!", A.GREEN)])


def s_summary(fig, ax, lt, dur):
    F.confetti(ax, lt, 0.1)
    F.PT(ax, 4.5, 13.7, "三关 · 全通关!", lt, 0.1, 52, A.GOLD)
    pop(ax, 4.5, 12.2, "压轴 BOSS 已击败", lt, 0.5, F.RED, size=30, rise=0.0, hold=2.5)
    rows = [("①", A.BLUE,  r"$y=4\,\mathrm{e}^{\frac{\pi}{2}}\!\left(x-\frac{\pi}{2}\right)$"),
            ("②", A.GOLD,  r"$a\in\left(-\infty,-\mathrm{e}^{-\frac{\pi}{2}}\right]\cup\left[1,+\infty\right)$"),
            ("③", A.GREEN, r"$x_1+x_2+x_3>\frac{3\pi}{4}$")]
    y = 10.4
    for i, (idx, col, ans) in enumerate(rows):
        t0 = 0.8 + i * 0.6
        A.chip(ax, 2.0, y, idx, col, lt, t0)
        a = A.appear(lt, t0 + 0.15, 0.5)
        if a > 0.02:
            ax.text(5.3, y, ans, color=A.rgba(col, a), fontsize=27, ha="center", va="center",
                    weight="bold", zorder=8,
                    bbox=dict(boxstyle="round,pad=0.45", fc=A.rgba(col, 0.1 * a),
                              ec=A.rgba(col, 0.7 * a), lw=1.5))
        y -= 1.65
    A.T(ax, 4.5, 4.5, "完整解析 · 关注主页 · 点赞收藏", lt, 3.2, 25, A.MUTED, ha="center", dur=0.4)
    draw_mascot(ax, 4.5, 2.0, 1.0, "thumbsup" if lt > 2.6 else "cheer", lt)


# ----------------------------------------------------------------------------- timeline
def _card(idx, title, color):
    return lambda fig, ax, lt, dur: card(ax, lt, idx, title, color)

def _clear(idx, color, xp, final=False):
    return lambda fig, ax, lt, dur: clear_scene(ax, lt, idx, color, xp, final)

TIMELINE = [
    ("hook",    s_hook,                              6.0),
    ("card1",   _card("①", "切线方程", A.BLUE),       2.5),
    ("part1",   s_part1,                             32.0),
    ("clear1",  _clear("①", A.BLUE, 500),             3.0),
    ("card2",   _card("②", "取值范围", A.GOLD),       2.5),
    ("part2",   s_part2,                             38.0),
    ("clear2",  _clear("②", A.GOLD, 800),             3.0),
    ("card3",   _card("③", "不等式证明", A.GREEN),     2.5),
    ("part3",   s_part3,                             44.0),
    ("clear3",  _clear("③", A.GREEN, 1500, True),     4.0),
    ("summary", s_summary,                           12.0),
]
TOTAL = sum(d for _, _, d in TIMELINE)   # 149.5s


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
    dx = dy = 0.0
    if name.startswith("clear"):
        dx, dy = F.shake(lt, 0.45, 0.5, 0.16)
    elif name == "hook":
        dx, dy = F.shake(lt, 0.2, 0.4, 0.08)
    ax = overlay(fig, dx, dy)
    fn(fig, ax, lt, d)
    if not name.startswith("card") and name != "summary":
        boss_bar(ax, gt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", type=float, default=None)
    ap.add_argument("--out", default="qf2.png")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--dpi", type=int, default=100)
    args = ap.parse_args()
    fig = plt.figure(figsize=(W, H), dpi=args.dpi)
    if args.at is not None:
        render_frame(fig, args.at)
        fig.savefig(args.out, facecolor=A.BG)
        print("wrote", args.out, "at t=", args.at)
        return
    os.makedirs(FRAMES_DIR, exist_ok=True)
    n = int(TOTAL * args.fps)
    print(f"rendering {n} frames ({TOTAL}s)")
    for i in range(n):
        render_frame(fig, i / args.fps)
        fig.savefig(os.path.join(FRAMES_DIR, f"f{i:05d}.png"), facecolor=A.BG)
        if i % 100 == 0:
            print(f"  {i}/{n}")
    print("done")


if __name__ == "__main__":
    main()
