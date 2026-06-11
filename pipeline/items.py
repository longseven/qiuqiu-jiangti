# -*- coding: utf-8 -*-
"""storyboard item 渲染动词分发。

每个 item 形如 {"t": 0.42 | "@sent:3" | "@sent:3+0.5", "type": "...", ...},
t 解析为场景内秒数由 ctx.resolve 完成(相对进度 0~1 或台词句锚点)。
"""
import math
import re

import matplotlib.patches as mp

from . import fx, graphs
from .core import C, T, appear, boxed, chip, clamp, ease_back, rgba


class Ctx:
    """单帧渲染上下文:场景数据 + 时间 + 锚点解析。"""

    def __init__(self, scene, timing, lt, gt):
        self.scene = scene          # storyboard 场景 dict
        self.timing = timing        # timeline 场景 dict: start/dur/audio_start/sents
        self.lt = lt                # 场景内秒
        self.gt = gt                # 全局秒
        self.dur = timing["dur"]

    _SENT = re.compile(r"^@sent:(\d+)(?:([+-])(\d+(?:\.\d+)?))?$")

    def resolve(self, t):
        """锚点 -> 场景内秒数。float = 相对进度;"@sent:N[±off]" = 第 N 句台词起点。"""
        if t is None:
            return 0.0
        if isinstance(t, (int, float)):
            return float(t) * self.dur
        m = self._SENT.match(str(t).strip())
        if not m:
            raise ValueError(f"非法时间锚点 {t!r}(场景 {self.scene.get('id')})")
        n = int(m.group(1))
        off = float(m.group(3) or 0.0) * (-1 if m.group(2) == "-" else 1)
        sents = self.timing.get("sents") or []
        if not sents:
            return 0.3 * self.dur + off          # 无句锚信息时的保守回退
        idx = min(n - 1, len(sents) - 1)
        return sents[idx] + off

    def col(self, name, default=None):
        return C.resolve(name, default)


# ----------------------------------------------------------------------------- 各类 item
def it_text(ctx, fig, ax, it):
    """淡入上浮文本(可含 mathtext)。"""
    t0 = ctx.resolve(it.get("t"))
    T(ax, it["pos"][0], it["pos"][1], it.get("tex") or it.get("text", ""),
      ctx.lt, t0, it.get("size", 20), ctx.col(it.get("color")),
      ha=it.get("ha", "center"), weight=it.get("weight", "normal"),
      dur=it.get("fade", 0.55))


def it_formula(ctx, fig, ax, it):
    """滑入公式/大字(full2 推导行的默认入场)。"""
    t0 = ctx.resolve(it.get("t"))
    fx.ST(ax, it["pos"][0], it["pos"][1], it.get("tex") or it.get("text", ""),
          ctx.lt, t0, it.get("size", 22), ctx.col(it.get("color")),
          ha=it.get("ha", "center"), dur=it.get("fade", 0.5))


def it_bigtext(ctx, fig, ax, it):
    """弹性放大大标题。"""
    t0 = ctx.resolve(it.get("t"))
    fx.PT(ax, it["pos"][0], it["pos"][1], it.get("text", ""),
          ctx.lt, t0, it.get("size", 40), ctx.col(it.get("color")))


def it_boxed(ctx, fig, ax, it):
    """圆角框文本(柔和版,summary 行用)。"""
    t0 = ctx.resolve(it.get("t"))
    boxed(ax, it["pos"][0], it["pos"][1], it.get("tex") or it.get("text", ""),
          ctx.lt, t0, it.get("size", 22), ctx.col(it.get("color")))


def it_answer(ctx, fig, ax, it):
    """答案揭晓三连:弹框 + 星爆 + 喝彩飘字。"""
    t0 = ctx.resolve(it.get("t"))
    color = ctx.col(it.get("color"), C.GOLD)
    x, y = it["pos"]
    fx.boxed_pop(ax, x, y, it.get("tex") or it.get("text", ""),
                 ctx.lt, t0, it.get("size", 30), color)
    fx.starburst(ax, x, y, ctx.lt, t0 + 0.2, color)
    cheer = it.get("cheer", "漂亮!")
    if cheer:
        cx, cy = it.get("cheer_pos", [x + 3.0, y + 0.7])
        fx.pop(ax, cx, cy, cheer, ctx.lt, t0 + 0.4, C.PINK, size=30)


def it_tag(ctx, fig, ax, it):
    t0 = ctx.resolve(it.get("t"))
    fx.tag(ax, it["pos"][0], it["pos"][1], it.get("text", ""),
           ctx.col(it.get("color"), C.RED), ctx.lt, t0, it.get("size", 20))


def it_pop(ctx, fig, ax, it):
    t0 = ctx.resolve(it.get("t"))
    fx.pop(ax, it["pos"][0], it["pos"][1], it.get("text", ""), ctx.lt, t0,
           ctx.col(it.get("color")), size=it.get("size", 28),
           rise=it.get("rise", 1.0), hold=it.get("hold", 1.2), bg=it.get("bg", False))


def it_chip(ctx, fig, ax, it):
    t0 = ctx.resolve(it.get("t"))
    chip(ax, it["pos"][0], it["pos"][1], it.get("text", ""),
         ctx.col(it.get("color")), ctx.lt, t0)


def it_fx(ctx, fig, ax, it):
    """通用特效触发:starburst / confetti / sparkles / score_pop / flash。"""
    t0 = ctx.resolve(it.get("t"))
    name = it.get("name")
    pos = it.get("pos", [4.5, 8.0])
    color = ctx.col(it.get("color"), C.GOLD)
    if name == "starburst":
        fx.starburst(ax, pos[0], pos[1], ctx.lt, t0, color)
    elif name == "confetti":
        fx.confetti(ax, ctx.lt, t0)
    elif name == "sparkles":
        fx.sparkles(ax, pos[0], pos[1], ctx.lt, t0)
    elif name == "score_pop":
        fx.score_pop(ax, pos[0], pos[1], ctx.lt, t0, it.get("text", "+100"), color)
    elif name == "flash":
        fx.flash(ax, ctx.lt - t0)
    else:
        raise KeyError(f"未知特效 {name!r}(场景 {ctx.scene.get('id')})")


def it_graph(ctx, fig, ax, it):
    """题型图象插件。rect 缺省用 part 模板的底部图位。"""
    rect = it.get("rect", [0.13, 0.045, 0.74, 0.255])
    gax = fig.add_axes(rect)
    graphs.resolve(it["plugin"])(gax, ctx.lt, ctx.dur, it.get("params", {}))


def it_mascot(ctx, fig, ax, it):
    """球球单次摆放(模板未覆盖的自由用法)。"""
    from .mascot import draw_mascot
    t0 = ctx.resolve(it.get("t"))
    if ctx.lt < t0:
        return
    draw_mascot(ax, it.get("pos", [4.5, 4.6])[0], it.get("pos", [4.5, 4.6])[1],
                it.get("s", 1.0), it.get("expr", "happy"), ctx.lt)


def it_bubble(ctx, fig, ax, it):
    t0 = ctx.resolve(it.get("t"))
    fx.bubble(ax, it["pos"][0], it["pos"][1], it.get("text", ""), ctx.lt, t0,
              ctx.col(it.get("color"), C.BLUE), hold=it.get("hold", 2.0))


def _check_lines(ax, x, y, s, color, lt, t0, z=9):
    """画线版对勾(✓ 字符在多数字体下变方块,lint 禁用)。"""
    a = appear(lt, t0, 0.3)
    if a <= 0.05:
        return
    p = ease_back(clamp((lt - t0) / 0.35))
    pts = [(x, y), (x + 0.14 * s * p, y - 0.14 * s * p), (x + 0.40 * s * p, y + 0.22 * s * p)]
    ax.plot([q[0] for q in pts], [q[1] for q in pts], color=rgba(color, a), lw=5,
            solid_capstyle="round", solid_joinstyle="round", zorder=z)


def it_quiz(ctx, fig, ax, it):
    """互动选择题:问题药丸 + A/B/C 选项 + 3-2-1 倒计时圆环 + 揭晓。

    {"t": "@sent:2", "reveal": "@sent:3", "type": "quiz",
     "question": "...", "options": ["...", "...", "..."], "answer": 0,
     "countdown": 3, "pos": [4.5, 10.2]}
    """
    lt = ctx.lt
    t0 = ctx.resolve(it.get("t"))
    reveal = ctx.resolve(it.get("reveal", it.get("t")))
    if lt < t0 or lt > reveal + it.get("hold_after", 2.4):
        return
    x, y = it.get("pos", [4.5, 10.2])
    accent = ctx.col(it.get("color"), C.BLUE)
    fx.tag(ax, x, y, it.get("question", ""), accent, lt, t0, size=it.get("size", 22))
    labels = "ABC"
    ans = int(it.get("answer", 0))
    revealed = lt >= reveal
    for k, opt in enumerate(it.get("options", [])):
        ty = y - 1.0 - 0.92 * k
        a, dx = fx.slide_in(lt, t0 + 0.2 + 0.12 * k, 0.4)
        if a <= 0.02:
            continue
        col, txt_a, lw = accent, a, 1.6
        if revealed:
            p = clamp((lt - reveal) / 0.4)
            if k == ans:
                col, lw = C.GREEN, 2.4
            else:
                txt_a = a * (1 - 0.62 * p)
        ax.text(x + dx, ty, f"{labels[k]}.  {opt}", color=rgba(col, txt_a),
                fontsize=it.get("opt_size", 20), ha="center", va="center",
                weight="bold", zorder=8,
                bbox=dict(boxstyle="round,pad=0.42", fc=rgba(col, 0.10 * txt_a),
                          ec=rgba(col, 0.8 * txt_a), lw=lw))
        if revealed and k == ans:
            _check_lines(ax, x + 2.55, ty - 0.1, 1.0, C.GREEN, lt, reveal)
    if revealed:
        fx.starburst(ax, x, y - 1.0 - 0.92 * ans, lt, reveal + 0.1, C.GREEN, R=1.6)
    # 倒计时圆环 + 数字
    cd = int(it.get("countdown", 3))
    if reveal - cd <= lt < reveal:
        remain = reveal - lt
        num = int(math.ceil(remain))
        frac = remain - int(remain) if remain != int(remain) else 1.0
        cx_, cy_ = it.get("cd_pos", [7.7, y])
        ax.add_patch(mp.Circle((cx_, cy_), 0.62, fc=rgba(C.GPANEL, 0.9),
                     ec=rgba(accent, 0.4), lw=2, zorder=9))
        ax.add_patch(mp.Wedge((cx_, cy_), 0.62, 90, 90 + 360 * frac,
                     width=0.10, fc=accent, ec="none", zorder=10))
        pulse = 1.0 + 0.25 * (1 - frac)
        ax.text(cx_, cy_, str(num), color=accent, fontsize=30 * pulse, ha="center",
                va="center", weight="bold", zorder=11)


def it_danmaku(ctx, fig, ax, it):
    """弹幕飘字:右进左出。{"t":0.3,"type":"danmaku","text":"学到了!","lane":0}"""
    lt = ctx.lt
    t0 = ctx.resolve(it.get("t"))
    dur = it.get("dur", 4.0)
    p = (lt - t0) / dur
    if p <= 0 or p >= 1:
        return
    y = it.get("y", 13.75 - 0.6 * int(it.get("lane", 0)))
    x = 10.8 - 13.5 * p
    a = min(1.0, 4 * p, 4 * (1 - p))
    col = ctx.col(it.get("color"), C.MUTED)
    ax.text(x, y, it.get("text", ""), color=rgba("#ffffff", 0.95 * a), fontsize=16,
            ha="center", va="center", weight="bold", zorder=9,
            bbox=dict(boxstyle="round,pad=0.32", fc=rgba(col, 0.75 * a), ec="none"))


ITEM_TYPES = {
    "text": it_text,
    "formula": it_formula,
    "bigtext": it_bigtext,
    "boxed": it_boxed,
    "answer": it_answer,
    "tag": it_tag,
    "pop": it_pop,
    "chip": it_chip,
    "fx": it_fx,
    "graph": it_graph,
    "mascot": it_mascot,
    "bubble": it_bubble,
    "quiz": it_quiz,
    "danmaku": it_danmaku,
}


def draw_items(ctx, fig, ax, items=None):
    for it in (items if items is not None else ctx.scene.get("items", [])):
        fn = ITEM_TYPES.get(it.get("type"))
        if fn is None:
            raise KeyError(f"未知 item 类型 {it.get('type')!r}(场景 {ctx.scene.get('id')})")
        fn(ctx, fig, ax, it)
