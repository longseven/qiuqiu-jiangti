# -*- coding: utf-8 -*-
"""storyboard 静态校验:结构 + mathtext 禁用清单 + 离屏试渲染。

三道门里的"渲染正确性硬门槛":所有问题在进帧渲染前拦截。
LLM 起草分镜时必跑;exit code != 0 即打回。

CLI:
  python -m pipeline.lint storyboards/xxx.json
"""
import argparse
import json
import re
import sys

from . import graphs
from .core import THEMES, Theme
from .dub import LEAD, MOCK_CPS, TAIL, split_sentences
from .items import ITEM_TYPES
from .mascot import EXPRESSIONS
from .sfx import SFX
from .templates import TEMPLATES

MASCOT_ACTIONS = {"roll_in"}

# ----------------------------------------------------------------------------- mathtext 规则表
# (README「改动须知」+ 实际踩坑的机器可查版;LLM 起草分镜直接复用)
MATHTEXT_DENY = [
    (re.compile(r"\\tfrac"), r"mathtext 不支持 \tfrac,用 \frac 或 \dfrac"),
    (re.compile(r"\\text\s*\{"), r"mathtext 不支持 \text{},中文/文字移到公式外"),
    (re.compile(r"\\begin\s*\{"), r"mathtext 不支持 \begin{} 环境"),
    (re.compile(r"[一-鿿]"), "公式($...$ 内)不能放中文,移到公式外"),
    (re.compile(r"[✓✔✗✘ˣ]"), "✓/✗/ˣ 等字符渲染成方块,用画线组件或普通文本替代"),
]
# 公式外也会变方块的字符(多数 CJK 字体没有这些字形)
TEXT_WARN = [
    (re.compile(r"[✓✔✗✘ˣ]"), "✓/✗/ˣ 在部分字体下变方块,建议用画线组件"),
]

_MATH_SEG = re.compile(r"\$([^$]*)\$")

VALID_COLORS = set(Theme.NAMES)
FX_NAMES = {"starburst", "confetti", "sparkles", "score_pop", "flash"}
POS_REQUIRED = {"text", "formula", "bigtext", "boxed", "answer", "tag",
                "pop", "chip", "bubble"}                  # 这些 item 渲染时直接取 it["pos"]
# 场景级已知字段(白名单;拼错字段名静默被 .get 吞掉,这里给警告)
SCENE_KEYS = {"id", "template", "accent", "narration", "min_dur", "max_dur",
              "items", "mascot", "graph", "title", "idx", "tag", "formula",
              "subtitle", "bubble", "xp", "combo", "crit", "crit_at", "final",
              "rows", "cta", "subtitle_pop", "clear_title", "start_text",
              "shake", "expr", "boss_intro", "game"}


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def err(self, where, msg):
        self.errors.append(f"[{where}] {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"[{where}] {msg}")

    @property
    def ok(self):
        return not self.errors


def _check_color(rep, where, c):
    if c is None:
        return
    if isinstance(c, str) and (c in VALID_COLORS or re.fullmatch(r"#[0-9a-fA-F]{6}", c)):
        return
    rep.err(where, f"非法颜色 {c!r}(语义名 {sorted(VALID_COLORS)} 或 #rrggbb)")


def _check_anchor(rep, where, t, n_sents):
    if t is None:
        return
    if isinstance(t, (int, float)):
        if not (0 <= float(t) <= 1):
            rep.err(where, f"相对锚点 t={t} 应在 0~1")
        return
    m = re.fullmatch(r"@sent:(\d+)(?:[+-]\d+(?:\.\d+)?)?", str(t).strip())
    if not m:
        rep.err(where, f"非法锚点 {t!r}(应为 0~1 浮点或 '@sent:N[±off]')")
        return
    n = int(m.group(1))
    if n < 1 or n > n_sents:
        rep.err(where, f"锚点 {t!r} 超出台词句数(共 {n_sents} 句)")


def _check_mathtext(rep, where, s):
    """禁用清单 + $ 配平。"""
    if s.count("$") % 2 != 0:
        rep.err(where, f"$ 不配对: {s!r}")
        return
    for seg in _MATH_SEG.findall(s):
        for pat, msg in MATHTEXT_DENY:
            if pat.search(seg):
                rep.err(where, f"{msg}: ${seg}$")
    outside = _MATH_SEG.sub("", s)
    for pat, msg in TEXT_WARN:
        if pat.search(outside):
            rep.warn(where, f"{msg}: {s!r}")


def _try_render(rep, texts):
    """离屏渲染每条文本,捕获 mathtext 异常(渲染正确性硬门槛)。"""
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(4, 1), dpi=60)
    try:
        for where, s in texts:
            fig.clf()
            try:
                fig.text(0.5, 0.5, s, fontsize=12)
                fig.canvas.draw()
            except Exception as e:
                rep.err(where, f"试渲染失败: {e} <- {s!r}")
    finally:
        plt.close(fig)


def lint(storyboard):
    rep = Report()
    meta = storyboard.get("meta")
    if not isinstance(meta, dict):
        rep.err("meta", "缺少 meta")
        return rep
    if meta.get("theme", "paper") not in THEMES:
        rep.err("meta", f"未知主题 {meta.get('theme')!r}")
    scenes = storyboard.get("scenes")
    if not scenes:
        rep.err("scenes", "缺少 scenes")
        return rep

    ids = set()
    texts = []      # 待试渲染 (where, str)
    for si, sc in enumerate(scenes):
        sid = sc.get("id") or f"#{si}"
        where = f"scene {sid}"
        if sc.get("id") in ids:
            rep.err(where, "场景 id 重复")
        ids.add(sc.get("id"))
        tpl = sc.get("template")
        if tpl not in TEMPLATES:
            rep.err(where, f"未知模板 {tpl!r}(可用 {sorted(TEMPLATES)})")
            continue
        _check_color(rep, where, sc.get("accent"))
        for k in set(sc) - SCENE_KEYS:
            rep.warn(where, f"未知字段 {k!r}(拼写错误会被静默忽略)")
        mind = float(sc.get("min_dur", 2.5))
        maxd = float(sc.get("max_dur", max(mind, 60.0)))
        if mind > maxd:
            rep.err(where, f"min_dur {mind} > max_dur {maxd}")
        if sc.get("crit") and float(sc.get("crit_at", 0.5)) >= mind:
            rep.err(where, f"crit_at {sc.get('crit_at', 0.5)} 超出场景最短时长 {mind}")
        if sc.get("narration") is not None and not isinstance(sc["narration"], str):
            rep.err(where, f"narration 应为字符串,得到 {type(sc['narration']).__name__}")
            continue
        narration = (sc.get("narration") or "").strip()
        sents = split_sentences(narration)
        est = LEAD + (len(re.sub(r"\s", "", narration)) / MOCK_CPS if narration else 0) + TAIL
        if narration and est > maxd:
            rep.warn(where, f"台词约 {est:.0f}s,可能超出 max_dur {maxd}s,建议拆段或精简")

        # 模板字段里的文本
        for k in ("title", "formula", "subtitle", "tag", "cta", "subtitle_pop",
                  "clear_title", "combo"):
            v = sc.get(k)
            if isinstance(v, str) and v:
                _check_mathtext(rep, f"{where}.{k}", v)
                texts.append((f"{where}.{k}", v))
        for ri, row in enumerate(sc.get("rows", [])):
            _check_color(rep, f"{where}.rows[{ri}]", row.get("accent"))
            if row.get("tex"):
                _check_mathtext(rep, f"{where}.rows[{ri}]", row["tex"])
                texts.append((f"{where}.rows[{ri}]", row["tex"]))

        # graph
        g = sc.get("graph")
        if g:
            try:
                graphs.resolve(g.get("plugin", ""))
            except KeyError as e:
                rep.err(f"{where}.graph", str(e))
            if not isinstance(g.get("params", {}), dict):
                rep.err(f"{where}.graph", "params 应为对象")

        # BOSS 登场
        bi = sc.get("boss_intro")
        if bi:
            _check_anchor(rep, f"{where}.boss_intro", bi.get("t"), len(sents))
            for txt in [bi.get("name")] + list(bi.get("skills", [])):
                if txt:
                    texts.append((f"{where}.boss_intro", txt))

        # mascot 块
        msc = sc.get("mascot")
        if msc:
            enter = msc.get("enter")
            if enter and enter.get("action") not in MASCOT_ACTIONS:
                rep.err(f"{where}.mascot.enter",
                        f"未知动作 {enter.get('action')!r}(可用 {sorted(MASCOT_ACTIONS)})")
            for mi, m in enumerate(msc.get("moods", [])):
                if m.get("expr") not in EXPRESSIONS:
                    rep.err(f"{where}.moods[{mi}]",
                            f"未知表情 {m.get('expr')!r}(可用 {EXPRESSIONS})")
                _check_anchor(rep, f"{where}.moods[{mi}]", m.get("t"), len(sents))
            for li, line in enumerate(msc.get("lines", [])):
                if not line.get("text"):
                    rep.err(f"{where}.lines[{li}]", "缺 text")
                else:
                    texts.append((f"{where}.lines[{li}]", line["text"]))
                _check_color(rep, f"{where}.lines[{li}]", line.get("color"))
                _check_anchor(rep, f"{where}.lines[{li}]", line.get("t"), len(sents))

        # hook bubble
        if sc.get("bubble"):
            b = sc["bubble"]
            _check_anchor(rep, f"{where}.bubble", b.get("t"), len(sents))
            _check_color(rep, f"{where}.bubble", b.get("color"))
            if b.get("text"):
                texts.append((f"{where}.bubble", b["text"]))
            else:
                rep.err(f"{where}.bubble", "bubble 缺 text")

        # items
        for ii, it in enumerate(sc.get("items", [])):
            iw = f"{where}.items[{ii}]"
            ity = it.get("type")
            if ity not in ITEM_TYPES:
                rep.err(iw, f"未知 item 类型 {ity!r}(可用 {sorted(ITEM_TYPES)})")
                continue
            _check_anchor(rep, iw, it.get("t"), len(sents))
            _check_color(rep, iw, it.get("color"))
            if ity == "fx" and it.get("name") not in FX_NAMES:
                rep.err(iw, f"未知特效 {it.get('name')!r}(可用 {sorted(FX_NAMES)})")
            if ity == "graph":
                try:
                    graphs.resolve(it.get("plugin", ""))
                except KeyError as e:
                    rep.err(iw, str(e))
            if ity == "quiz":
                opts = it.get("options")
                if not it.get("question"):
                    rep.err(iw, "quiz 缺 question")
                if not isinstance(opts, list) or not (2 <= len(opts) <= 3):
                    rep.err(iw, "quiz options 应为 2~3 个选项")
                else:
                    ans = it.get("answer")
                    if not isinstance(ans, int) or not (0 <= ans < len(opts)):
                        rep.err(iw, f"quiz answer={ans!r} 越界")
                    for o in opts:
                        _check_mathtext(rep, iw, str(o))
                        texts.append((iw, str(o)))
                _check_anchor(rep, f"{iw}.reveal", it.get("reveal"), len(sents))
                if it.get("question"):
                    _check_mathtext(rep, iw, it["question"])
                    texts.append((iw, it["question"]))
            sfx_name = it.get("sfx", "auto")
            if sfx_name not in (None, "auto") and sfx_name not in SFX:
                rep.err(iw, f"未知音效 {sfx_name!r}(可用 {sorted(SFX)})")
            s = it.get("tex") or it.get("text")
            if ity in ("text", "formula", "boxed", "answer", "bigtext", "tag",
                       "pop", "bubble", "danmaku") and not s:
                rep.err(iw, f"{ity} 缺 tex/text")
            if s:
                _check_mathtext(rep, iw, s)
                texts.append((iw, s))
            if ity in POS_REQUIRED and "pos" not in it:
                rep.err(iw, f"{ity} 必须给 pos [x, y](渲染时直接取用,缺失会崩)")
            if "pos" in it and (not isinstance(it["pos"], list) or len(it["pos"]) != 2):
                rep.err(iw, f"pos 应为 [x, y],得到 {it.get('pos')!r}")

        # 表情快捷校验:expr 字段
        if sc.get("expr") and sc["expr"] not in EXPRESSIONS:
            rep.err(where, f"未知表情 {sc['expr']!r}")

    if not rep.errors:        # 结构都对了才值得花时间试渲染
        _try_render(rep, texts)
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    args = ap.parse_args()
    with open(args.storyboard, encoding="utf-8") as f:
        sb = json.load(f)
    rep = lint(sb)
    for w in rep.warnings:
        print(f"WARN  {w}")
    for e in rep.errors:
        print(f"ERROR {e}")
    if rep.ok:
        print(f"lint OK ({len(rep.warnings)} warnings)")
    else:
        print(f"lint FAILED: {len(rep.errors)} errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
