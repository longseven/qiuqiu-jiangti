# -*- coding: utf-8 -*-
"""特效动词库(storyboard 可引用的"动词"),由 animate_fun.py / animate_fun_full2.py 重构。

所有函数自带时间守卫:不在生效区间内则什么都不画,可以无脑每帧调用。
颜色参数一律传具体色值(调用方先用 C.resolve 解析语义名)。
"""
import math
import random

import matplotlib.patches as mp
import matplotlib.pyplot as plt

from .core import C, appear, clamp, ease, ease_back, rgba

# ----------------------------------------------------------------------------- 入场
def slide_in(lt, t0, dur=0.5):
    """右侧滑入:返回 (alpha, dx)。"""
    p = clamp((lt - t0) / dur)
    if p <= 0.0:
        return 0.0, 1.5
    return clamp(p / 0.4), 1.5 * (1 - ease_back(p))


def ST(ax, x, y, s, lt, t0, size, color, ha="center", weight="bold", dur=0.5, z=7):
    """滑入大字(full2 公式的默认入场)。"""
    a, dx = slide_in(lt, t0, dur)
    if a <= 0.02:
        return
    ax.text(x + dx, y, s, color=rgba(color, a), fontsize=size, ha=ha, va="center",
            weight=weight, zorder=z)


def PT(ax, x, y, s, lt, t0, size, color=None, ha="center", dur=0.36, weight="bold", z=8):
    """弹性放大入场的大标题。"""
    color = color or C.WHITE
    p = clamp((lt - t0) / dur)
    if p <= 0.001:
        return
    sc = ease_back(p)
    a = clamp(p / 0.5)
    ax.text(x, y, s, color=rgba(color, a), fontsize=size * (0.6 + 0.4 * sc),
            ha=ha, va="center", weight=weight, zorder=z)


def boxed_pop(ax, x, y, s, lt, t0, size, color, z=8):
    """答案框:弹性放大 + 圆角框。"""
    b = clamp((lt - t0) / 0.4)
    if b <= 0.02:
        return
    ax.text(x, y, s, color=rgba(color, b), fontsize=size * (0.6 + 0.4 * ease_back(b)),
            ha="center", va="center", weight="bold", zorder=z,
            bbox=dict(boxstyle="round,pad=0.55", fc=rgba(color, 0.12 * b),
                      ec=rgba(color, 0.9 * b), lw=2.2))


def tag(ax, x, y, s, color, lt, t0, size=20, tc=None, ha="center"):
    """药丸标签(关卡标题等)。"""
    a = appear(lt, t0, 0.3)
    if a <= 0.003:
        return
    ax.text(x, y, s, color=rgba(tc or C.BG, a), fontsize=size, ha=ha, va="center",
            weight="bold", zorder=8,
            bbox=dict(boxstyle="round,pad=0.4", fc=rgba(color, a), ec="none"))


# ----------------------------------------------------------------------------- 瞬时弹出
def pop(ax, x, y, text, lt, t0, color, size=28, rise=1.0, hold=1.2, bg=False, z=10):
    """上浮渐隐的喝彩文字(「漂亮!」「+500 XP」)。"""
    p = (lt - t0) / hold
    if p <= 0 or p >= 1:
        return
    a = min(1.0, p / 0.18) * (1 - p) ** 0.5
    sc = ease_back(min(1.0, p / 0.25))
    kw = {}
    if bg:
        kw["bbox"] = dict(boxstyle="round,pad=0.4", fc=rgba("#ffffff", 0.85 * a), ec="none")
    ax.text(x, y + rise * ease(clamp(p)), text, color=rgba(color, a),
            fontsize=size * (0.5 + 0.5 * sc), ha="center", va="center",
            weight="bold", zorder=z, **kw)


def score_pop(ax, x, y, lt, t0, text="+100", color=None):
    color = color or C.GOLD
    p = (lt - t0) / 1.3
    if p <= 0 or p >= 1:
        return
    ax.text(x, y + 1.2 * ease(clamp(p)), text, color=rgba(color, 1 - p), fontsize=26,
            ha="center", va="center", weight="bold", zorder=9)


def starburst(ax, x, y, lt, t0, color, n=14, R=1.4):
    """星爆(答案揭晓)。"""
    p = (lt - t0) / 0.75
    if p <= 0 or p >= 1:
        return
    a = (1 - p) ** 0.7
    e = ease(clamp(p))
    xs = [x + R * e * math.cos(k / n * 2 * math.pi) for k in range(n)]
    ys = [y + R * e * math.sin(k / n * 2 * math.pi) for k in range(n)]
    ax.scatter(xs, ys, s=210 * (1 - 0.5 * p), marker="*", color=rgba(color, a),
               zorder=9, linewidths=0)


def sparkles(ax, cx, cy, lt, t0, n=12):
    """环绕闪烁星(关卡卡片)。"""
    if lt < t0:
        return
    fade = clamp((lt - t0) / 0.4)
    for k in range(n):
        ang = k / n * 2 * math.pi + 0.4
        r = 2.6 + 0.8 * ((k * 7) % 5) / 5
        tw = 0.4 + 0.6 * abs(math.sin(lt * 3.4 + k))
        ax.scatter([cx + r * math.cos(ang)], [cy + r * 0.7 * math.sin(ang)], s=110,
                   marker="*", color=rgba(C.GOLD, 0.78 * tw * fade), zorder=6, linewidths=0)


def bubble(ax, x, y, text, lt, t0, color=None, hold=2.0, size=20):
    """球球的对话泡。"""
    color = color or C.BLUE
    if not (t0 <= lt <= t0 + hold):
        return
    a = ease(clamp((lt - t0) / 0.28)) * clamp((t0 + hold - lt) / 0.3)
    if a <= 0.02:
        return
    ax.text(x, y, text, color=rgba("#ffffff", a), fontsize=size, ha="center", va="center",
            weight="bold", zorder=9,
            bbox=dict(boxstyle="round,pad=0.5", fc=rgba(color, a), ec="none"))
    ax.add_patch(mp.Polygon([[x - 0.3, y - 0.30], [x + 0.06, y - 0.30], [x - 0.5, y - 0.7]],
                 color=rgba(color, a), zorder=8))


# ----------------------------------------------------------------------------- 全屏
def shake(lt, t0, dur=0.45, amp=0.12):
    """震屏偏移 (dx, dy)。"""
    if t0 <= lt < t0 + dur:
        k = 1 - (lt - t0) / dur
        return amp * k * math.sin(45 * (lt - t0)), amp * k * math.cos(38 * (lt - t0))
    return 0.0, 0.0


def flash(ax, lt, dur=0.4, peak=0.6):
    """开场白闪。"""
    if lt < dur:
        ax.add_patch(plt.Rectangle((0, 0), 9, 16,
                     color=rgba("#ffffff", peak * (1 - lt / dur)), zorder=11))


# ----------------------------------------------------------------------------- 撒花
_CONFETTI = []


def init_confetti(seed=7):
    """生成确定性的彩纸粒子(颜色取自当前主题,换主题后需重调)。"""
    rng = random.Random(seed)
    pal = [C.GOLD, C.GREEN, C.BLUE, C.RED, "#a855f7", "#0891b2"]
    _CONFETTI.clear()
    for i in range(70):
        ang = rng.uniform(0, 2 * math.pi)
        spd = rng.uniform(2.2, 7.5)
        _CONFETTI.append(dict(
            vx=math.cos(ang) * spd * rng.uniform(0.6, 1.0),
            vy=abs(math.sin(ang)) * spd + rng.uniform(1.5, 4.0),
            x0=4.5 + rng.uniform(-1.2, 1.2),
            col=pal[i % len(pal)],
            sz=rng.uniform(50, 150),
        ))


def confetti(ax, lt, t0):
    if not _CONFETTI:
        init_confetti()
    tau = lt - t0
    if tau <= 0:
        return
    xs, ys, cs, ss = [], [], [], []
    for c in _CONFETTI:
        x = c["x0"] + c["vx"] * tau
        y = 8.2 + c["vy"] * tau - 4.6 * tau * tau
        if y < -1:
            continue
        xs.append(x); ys.append(y); cs.append(c["col"]); ss.append(c["sz"])
    if xs:
        a = clamp(1.3 - tau / 2.6)
        ax.scatter(xs, ys, s=ss, c=cs, marker="s", alpha=a, zorder=9, linewidths=0)


# ----------------------------------------------------------------------------- BOSS 形象
BOSS_BODY = "#8b1e3f"
BOSS_SPIKE = "#5b1027"
BOSS_EYE = "#ffe9a8"


def draw_boss(ax, cx, cy, s, t=0.0, z=7):
    """压轴 BOSS:带刺的暗红怪球(与球球同为手绘风,登场用)。"""
    cy = cy + 0.06 * s * math.sin(2 * math.pi * t / 2.1)
    # 尖刺
    n = 11
    for k in range(n):
        ang = k / n * 2 * math.pi + 0.28 + 0.04 * math.sin(t * 2 + k)
        r0, r1 = 0.92 * s, 1.32 * s
        half = 0.16
        pts = [(cx + r0 * math.cos(ang - half), cy + r0 * math.sin(ang - half)),
               (cx + r0 * math.cos(ang + half), cy + r0 * math.sin(ang + half)),
               (cx + r1 * math.cos(ang), cy + r1 * math.sin(ang))]
        ax.add_patch(mp.Polygon(pts, closed=True, fc=BOSS_SPIKE, ec="none", zorder=z))
    # 身体
    ax.add_patch(mp.Circle((cx, cy), s, fc=BOSS_BODY, ec=BOSS_SPIKE, lw=3, zorder=z + 1))
    # 怒眼(斜切白眼 + 竖瞳)
    for sgn in (-1, 1):
        ex, ey = cx + sgn * 0.36 * s, cy + 0.18 * s
        ax.add_patch(mp.Ellipse((ex, ey), 0.42 * s, 0.30 * s, angle=-18 * sgn,
                     fc=BOSS_EYE, ec="none", zorder=z + 2))
        ax.add_patch(mp.Ellipse((ex, ey - 0.02 * s), 0.10 * s, 0.22 * s,
                     fc="#23030c", ec="none", zorder=z + 3))
        ax.plot([ex + sgn * 0.30 * s, ex - sgn * 0.26 * s],
                [ey + 0.34 * s, ey + 0.12 * s],
                color=BOSS_SPIKE, lw=4, solid_capstyle="round", zorder=z + 4)
    # 锯齿嘴
    mx, my, w = cx, cy - 0.42 * s, 0.62 * s
    xs = [mx - w / 2 + w * i / 6 for i in range(7)]
    ys = [my + (0.10 * s if i % 2 else -0.04 * s) for i in range(7)]
    ax.plot(xs, ys, color="#23030c", lw=3.5, solid_capstyle="round",
            solid_joinstyle="round", zorder=z + 3)


# ----------------------------------------------------------------------------- BOSS 血条
def boss_hp(gt, crits):
    """HP ∈ [0,1]:在每个 crit 时刻(全局秒)掉一格,等分,最后一格归零。"""
    if not crits:
        return 1.0
    n = len(crits)
    hp = 1.0
    for i, ct in enumerate(crits):
        drop = 1.0 / n
        hp -= drop * ease(clamp((gt - ct) / 0.6))
    return max(0.0, hp)


def boss_bar(ax, gt, crits, label="压轴BOSS"):
    """顶部 BOSS 血条 + 暴击飘字(原 full2.boss_bar 的数据驱动版)。"""
    hp = boss_hp(gt, crits)
    ax.text(0.55, 15.33, label, color=C.RED, fontsize=18, ha="left", va="center",
            weight="bold", zorder=8)
    x, y, w, h = 2.75, 15.1, 3.85, 0.46
    ax.add_patch(mp.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                 fc=C.HPTRACK, ec=C.GRID, lw=1.4, zorder=7))
    if hp > 0.001:
        ax.add_patch(mp.FancyBboxPatch((x + 0.07, y + 0.07), max(0.001, (w - 0.14) * hp),
                     h - 0.14, boxstyle="round,pad=0.03", fc=C.RED, ec="none", zorder=8))
    ax.text(x + w + 0.22, y + h / 2, "KO" if hp <= 0.001 else f"{int(round(hp * 100))}%",
            color=C.RED, fontsize=18, ha="left", va="center", weight="bold", zorder=8)
    pct = int(round(100 / max(1, len(crits))))
    for ct in crits[:-1]:                      # 最后一击由 clear 场景的「KO」呈现
        if 0 <= gt - ct < 1.15:
            p = (gt - ct) / 1.15
            ax.text(4.5, 14.45 - 0.7 * ease(p), f"暴击 -{pct}%!", color=rgba(C.RED, 1 - p),
                    fontsize=32, ha="center", va="center", weight="bold", zorder=10)


def hp_bar(ax, frac, lt, label="挑战进度"):
    """左上角进度血条(单题短视频用)。"""
    a = appear(lt, 0.1, 0.4)
    if a <= 0.02:
        return
    x, y, w, h = 0.7, 15.2, 5.3, 0.46
    ax.add_patch(mp.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                 fc=rgba(C.HPTRACK, a), ec=rgba(C.GRID, a), lw=1.5, zorder=7))
    fillcol = C.HP if frac > 0.55 else (C.GOLD if frac > 0.3 else C.RED)
    ax.add_patch(mp.FancyBboxPatch((x + 0.08, y + 0.08), max(0.001, (w - 0.16) * frac),
                 h - 0.16, boxstyle="round,pad=0.04", fc=rgba(fillcol, a), ec="none", zorder=8))
    ax.text(x + w + 0.35, y + h / 2, f"{label} {int(round(frac * 100))}%",
            color=rgba(C.WHITE, a), fontsize=15, ha="left", va="center", weight="bold", zorder=9)
