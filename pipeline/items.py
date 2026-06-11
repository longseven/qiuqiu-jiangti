# -*- coding: utf-8 -*-
"""storyboard item 渲染动词分发。

每个 item 形如 {"t": 0.42 | "@sent:3" | "@sent:3+0.5", "type": "...", ...},
t 解析为场景内秒数由 ctx.resolve 完成(相对进度 0~1 或台词句锚点)。
"""
import re

from . import fx, graphs
from .core import C, T, boxed, chip


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
}


def draw_items(ctx, fig, ax, items=None):
    for it in (items if items is not None else ctx.scene.get("items", [])):
        fn = ITEM_TYPES.get(it.get("type"))
        if fn is None:
            raise KeyError(f"未知 item 类型 {it.get('type')!r}(场景 {ctx.scene.get('id')})")
        fn(ctx, fig, ax, it)
