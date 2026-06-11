# -*- coding: utf-8 -*-
"""五类场景模板:hook / card / part / clear / summary(由 animate_fun_full2 场景函数重构)。

模板决定底层布局与固定节目效果;内容(公式、台词、表情节拍)全部来自 storyboard。
每个模板:  fn(ctx, fig, ax)
"""
import math

from . import fx
from .core import C, T, appear, chip, clamp, ease, rgba
from .items import draw_items
from .mascot import draw_mascot

# 各模板的默认震屏(t0, dur, amp);engine 在建 axes 前查询
TEMPLATE_SHAKE = {
    "hook": (0.2, 0.4, 0.08),
    "clear": (0.45, 0.5, 0.16),
}


# ----------------------------------------------------------------------------- 球球台词块
def mascot_block(ctx, ax, spec, default_pos, default_s):
    """球球 + 表情节拍 + 对话泡。spec = scene["mascot"]:
    {"pos":[x,y], "s":0.68,
     "moods": [{"t":0,"expr":"think"}, ...],
     "lines": [{"t":0.07,"text":"...","color":"BLUE","bubble_pos":[x,y]}, ...]}
    """
    if spec is None:
        return
    pos = list(spec.get("pos", default_pos))
    s = spec.get("s", default_s)
    enter = spec.get("enter")
    if enter and enter.get("action") == "roll_in":      # 滚入场:左侧滑入 + 渐止小跳
        edur = float(enter.get("dur", 1.0))
        p = clamp(ctx.lt / max(edur, 1e-3))
        e = ease(p)
        x0 = enter.get("from_x", -1.5)
        pos[0] = x0 + (pos[0] - x0) * e
        pos[1] = pos[1] + 0.5 * s * abs(math.sin(2.6 * math.pi * e)) * (1 - e)
    expr = "happy"
    for m in spec.get("moods", []):
        if ctx.lt >= ctx.resolve(m.get("t", 0)):
            expr = m["expr"]
    draw_mascot(ax, pos[0], pos[1], s, expr, ctx.lt)
    default_bub = spec.get("bubble_pos", [pos[0] + 2.0, pos[1] + 0.55])
    for line in spec.get("lines", []):
        bp = line.get("bubble_pos", default_bub)
        fx.bubble(ax, bp[0], bp[1], line["text"], ctx.lt, ctx.resolve(line.get("t", 0)),
                  ctx.col(line.get("color"), C.BLUE), hold=line.get("hold", 2.0))


# ----------------------------------------------------------------------------- 模板
def hook(ctx, fig, ax):
    """开场钩子:标签 + 大标题 + 题面公式 + 三问导航 + 球球。"""
    sc = ctx.scene
    lt = ctx.lt
    accent = ctx.col(sc.get("accent"), C.BLUE)
    if sc.get("tag"):
        fx.tag(ax, 4.5, 13.4, sc["tag"], C.RED, lt, 0.3, 28)
    if sc.get("title"):
        fx.PT(ax, 4.5, 11.6, sc["title"], lt, 0.15, 60, accent)
    if sc.get("formula"):
        T(ax, 4.5, 9.9, sc["formula"], lt, 1.1, 29, accent, dur=0.4)
    if sc.get("subtitle"):
        T(ax, 4.5, 8.5, sc["subtitle"], lt, 1.9, 26, C.MUTED, dur=0.4)
    if sc.get("boss_intro"):
        bi = sc["boss_intro"]
        bt = ctx.resolve(bi.get("t", 0.18))
        if lt >= bt:
            bx, by = bi.get("pos", [4.5, 8.7])
            bs = bi.get("s", 0.85) * (0.6 + 0.4 * ease(clamp((lt - bt) / 0.4)))
            fx.draw_boss(ax, bx, by, bs, lt)
            if bi.get("name"):
                fx.tag(ax, bx, by - 1.9 * bi.get("s", 0.85), bi["name"], C.RED,
                       lt, bt + 0.3, 22)
            for i, sk in enumerate(bi.get("skills", [])):
                fx.pop(ax, bx - 2.6 + 2.6 * i, by + 1.75 * bi.get("s", 0.85),
                       sk, lt, bt + 0.6 + 0.35 * i, C.PINK, size=20, rise=0.5,
                       hold=2.2, bg=True)
    mascot_block(ctx, ax, sc.get("mascot", {
        "pos": [4.5, 4.6], "s": 1.1,
        "moods": [{"t": 0, "expr": "happy"}, {"t": 0.4, "expr": "cheer"}],
    }), [4.5, 4.6], 1.1)
    if sc.get("bubble"):
        b = sc["bubble"]
        fx.bubble(ax, b.get("pos", [6.5, 6.1])[0], b.get("pos", [6.5, 6.1])[1],
                  b["text"], lt, ctx.resolve(b.get("t", 0.43)),
                  ctx.col(b.get("color"), C.BLUE))
    draw_items(ctx, fig, ax)


def card(ctx, fig, ax):
    """关卡转场卡:关N + 标题 + START! + 欢呼球球。固定 2.5s,无台词。"""
    sc = ctx.scene
    lt = ctx.lt
    accent = ctx.col(sc.get("accent"), C.BLUE)
    fx.sparkles(ax, 4.5, 9.6, lt, 0.5, 13)
    fx.ST(ax, 4.5, 10.7, f"关 {sc.get('idx', '')}", lt, 0.1, 72, accent)
    fx.ST(ax, 4.5, 8.9, sc.get("title", ""), lt, 0.35, 44, C.WHITE)
    fx.pop(ax, 4.5, 7.1, sc.get("start_text", "START!"), lt, 0.7, accent,
           size=48, rise=0.0, hold=1.8)
    draw_mascot(ax, 4.5, 3.9, 1.2, "cheer" if lt > 0.6 else "happy", lt)
    draw_items(ctx, fig, ax)


def part(ctx, fig, ax):
    """讲解关卡:关卡标签 + 推导 items + 底部图象 + 球球解说。"""
    sc = ctx.scene
    lt = ctx.lt
    accent = ctx.col(sc.get("accent"), C.BLUE)
    fx.tag(ax, 4.5, 14.35, f"关{sc.get('idx', '')} · {sc.get('title', '')}",
           accent, lt, 0.0, 30)
    if sc.get("graph"):
        g = dict(sc["graph"])
        g.setdefault("type", "graph")
        draw_items(ctx, fig, ax, [g])
    draw_items(ctx, fig, ax)
    mascot_block(ctx, ax, sc.get("mascot"), [1.5, 6.4], 0.68)


def clear(ctx, fig, ax):
    """通关页:白闪(final)+ 撒花 + 通关标题 + XP/连击 + 球球点赞。"""
    sc = ctx.scene
    lt = ctx.lt
    accent = ctx.col(sc.get("accent"), C.BLUE)
    final = bool(sc.get("final"))
    if final and lt < 0.4:
        import matplotlib.pyplot as plt
        ax.add_patch(plt.Rectangle((0, 0), 9, 16,
                     color=rgba("#ffffff", 0.6 * (1 - lt / 0.4)), zorder=11))
    fx.confetti(ax, lt, 0.15)
    if final:
        fx.confetti(ax, lt, 0.7)
    title = sc.get("clear_title") or ("BOSS 击败!" if final else f"关{sc.get('idx', '')} 通关!")
    fx.ST(ax, 4.5, 10.6, title, lt, 0.1, 64 if final else 58,
          C.RED if final else accent, z=12)
    if sc.get("xp"):
        fx.pop(ax, 4.5, 8.6, f"+{sc['xp']} XP", lt, 0.6, C.GOLD, size=50, bg=True, z=12)
    if sc.get("combo"):
        fx.pop(ax, 4.5, 7.0, sc["combo"], lt, 0.95, C.RED, size=36, bg=True, z=12)
    draw_mascot(ax, 4.5, 3.9, 1.15, "thumbsup" if lt > 0.7 else "cheer", lt)
    draw_items(ctx, fig, ax)


def summary(ctx, fig, ax):
    """总结页:撒花 + 大标题 + 结论行(chip+框)+ CTA + 球球。"""
    sc = ctx.scene
    lt = ctx.lt
    fx.confetti(ax, lt, 0.1)
    if sc.get("title"):
        fx.PT(ax, 4.5, 13.7, sc["title"], lt, 0.1, 52, C.GOLD)
    if sc.get("subtitle_pop"):
        fx.pop(ax, 4.5, 12.2, sc["subtitle_pop"], lt, 0.5, C.RED, size=30, rise=0.0, hold=2.5)
    y = 10.4
    for i, row in enumerate(sc.get("rows", [])):
        t0 = 0.8 + i * 0.6
        col = ctx.col(row.get("accent"))
        chip(ax, 2.0, y, row.get("idx", ""), col, lt, t0)
        a = appear(lt, t0 + 0.15, 0.5)
        if a > 0.02:
            ax.text(5.3, y, row.get("tex", ""), color=rgba(col, a), fontsize=27,
                    ha="center", va="center", weight="bold", zorder=8,
                    bbox=dict(boxstyle="round,pad=0.45", fc=rgba(col, 0.1 * a),
                              ec=rgba(col, 0.7 * a), lw=1.5))
        y -= 1.65
    if sc.get("cta"):
        T(ax, 4.5, 4.5, sc["cta"], lt, 3.2, 25, C.MUTED, dur=0.4)
    draw_mascot(ax, 4.5, 2.0, 1.0, "thumbsup" if lt > 2.6 else "cheer", lt)
    draw_items(ctx, fig, ax)


TEMPLATES = {
    "hook": hook,
    "card": card,
    "part": part,
    "clear": clear,
    "summary": summary,
}
