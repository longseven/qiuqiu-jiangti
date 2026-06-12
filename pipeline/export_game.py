# -*- coding: utf-8 -*-
"""导出「边听边玩」H5 游戏:storyboard + timeline + TTS 音频 -> game/<名>/。

与视频共用同一份分镜与配音;讲解音频按句驱动游戏事件(@sent 锚点)。
互动定义来自 scene.game.interactions(视频渲染器忽略该字段);本题缺省
互动由 DEFAULT_INTERACTIONS 提供,P2 阶段并入 storyboard。

Usage:
  python -m pipeline.export_game storyboards/xxx.json --builddir build/xxx --outdir game/xxx
  (需先跑过 dub:依赖 timeline.json 与 audio 缓存 mp3)
"""
import argparse
import glob
import json
import math
import os
import re
import shutil

from .items import Ctx


def tex_plain(s):
    """mathtext -> 游戏 HUD 用纯文本(π/∞/∪/下标等)。"""
    s = str(s or "")
    s = s.replace("\\,", " ").replace("\\!", "").replace("\\;", " ")
    s = s.replace("\\quad", " ").replace("\\qquad", "  ")
    s = re.sub(r"\\mathrm\{([^{}]*)\}", r"\1", s)
    for _ in range(3):                                   # 嵌套分式逐层展开
        s = re.sub(r"\\[dt]?frac\{([^{}]+)\}\{([^{}]+)\}", r"\1/\2", s)
    s = (s.replace("\\pi", "π").replace("\\infty", "∞").replace("\\cup", "∪")
          .replace("\\in", "∈").replace("\\left", "").replace("\\right", "")
          .replace("\\cos", "cos").replace("\\sin", "sin").replace("\\sqrt", "√"))
    s = re.sub(r"\^\{([^{}]+)\}", r"^(\1)", s)
    s = re.sub(r"_\{?1\}?", "₁", s)
    s = re.sub(r"_\{?2\}?", "₂", s)
    s = re.sub(r"_\{?3\}?", "₃", s)
    s = re.sub(r"[${}]", "", s)
    return re.sub(r"\s+", " ", s).strip()

# 本题缺省互动(scene.game 缺失时注入;选项可用 ^ 上标记号,由前端排版)
# 每关 3 个互动点,quiz 尽量压在台词自带的"三、二、一!"悬念节拍上
DEFAULT_INTERACTIONS = {
    "part1": [
        {"at_sent": 3, "type": "quiz",
         "question": "切点的纵坐标 f(π/2) 是多少?",
         "options": ["0", "4e^(π/2)", "-1"], "answer": 0,
         "hint": "代入 x=π/2:cos(3π/2) 和 cos(π/2) 都等于 0,两项全灭!"},
        {"at_sent": 6, "type": "quiz",
         "question": "对 eˣ·cos3x 这种乘积求导,正确姿势是?",
         "options": ["两项分别求导再交叉相加", "只对 cos3x 求导就行", "先代 x=π/2 再求导"],
         "answer": 0,
         "hint": "乘积法则 (uv)'=u'v+uv',漏一项斜率直接报废!"},
        {"at_sent": 7, "type": "tangent_shot",
         "hint": "斜率是 4e^(π/2),很陡!把准星拧到和曲线刚好贴上"},
    ],
    "part2": [
        {"at_sent": 4, "type": "quiz",
         "question": "h(t) 在 (0, π/2) 上的走势是?",
         "options": ["一路下降", "先升后降", "一路上升"], "answer": 0,
         "hint": "h'(t)<0 恒成立,从 h(0)=1 一路滑到 -e^(-π/2)"},
        {"at_sent": 5, "type": "range_lock",
         "hint": "把 a 拖出 (-e^(-π/2), 1) 这个值域区间,曲线就碰不到横线了"},
        {"at_sent": 6, "type": "quiz",
         "question": "a 恰好等于 1,(0, π/2) 上 f 还有零点吗?",
         "options": ["没有,开区间两头取不到", "有,t 靠近 0 就撞上", "有,中间某处相切"],
         "answer": 0,
         "hint": "值域是开区间 (-e^(-π/2), 1),1 本身取不到,a=1 照样安全!"},
    ],
    "part3": [
        {"at_sent": 4, "type": "quiz",
         "question": "g(x)<0 的区间是?",
         "options": ["(π/12, 5π/12)", "(0, π/4)", "(π/4, π/2)"], "answer": 0,
         "hint": "cos(3x+π/4)<0 ⟺ 3x+π/4 ∈ (π/2, 3π/2),解出来就是山谷"},
        {"at_sent": 5, "type": "quiz",
         "question": "如果没有 eˣ 这个因子,等高两点 x₁+x₃ 等于?",
         "options": ["π/2(山谷对称)", "3π/4", "π/4"], "answer": 0,
         "hint": "纯余弦的山谷关于 π/4 对称,对称两点之和 = 2×π/4 = π/2"},
        {"at_sent": 7, "type": "valley_drag",
         "hint": "先把 x₃ 拖到和 x₁ 等高,再把 x₂ 拖到谷底偏右、切线平行虚线的位置"},
    ],
}


def _math_constants():
    """游戏判定所需的数学事实(单一来源:graphs.derivative)。"""
    from .graphs.derivative import P3
    x1, x2, x3, L = P3
    return {
        "slope1": 4 * math.exp(math.pi / 2),            # 第①关真实斜率
        "h_top": 1.0,                                    # 第②关值域上界
        "h_bot": -math.exp(-math.pi / 2),                # 第②关值域下界
        "p3": {"x1": x1, "x2": x2, "x3": x3, "L": L},   # 第③关三点
        "target3": 3 * math.pi / 4,
    }


def export(storyboard_path, builddir, outdir):
    with open(storyboard_path, encoding="utf-8") as f:
        sb = json.load(f)
    tl_path = os.path.join(builddir, "timeline.json")
    with open(tl_path, encoding="utf-8") as f:
        tl = json.load(f)
    if tl.get("mock"):
        raise SystemExit("timeline 是 mock 的(无音频),先跑真实 dub 再导出游戏")
    timing = {t["id"]: t for t in tl["scenes"]}

    os.makedirs(os.path.join(outdir, "audio"), exist_ok=True)
    scenes_out = []
    for sc in sb["scenes"]:
        tm = timing[sc["id"]]
        ctx = Ctx(sc, tm, 0.0, 0.0)
        a0 = tm.get("audio_start", 0.0)
        # 音频文件:dub 缓存按 id-哈希 命名,复制为稳定名
        audio_rel = None
        if tm.get("audio_dur", 0) > 0:
            cands = sorted(glob.glob(os.path.join(builddir, "audio", f"{sc['id']}-*.mp3")))
            if not cands:
                raise SystemExit(f"缺少场景 {sc['id']} 的音频缓存,先跑 dub")
            audio_rel = f"audio/{sc['id']}.mp3"
            shutil.copy(cands[-1], os.path.join(outdir, audio_rel))
        # 球球台词泡 -> 音频相对秒
        bubbles = []
        for line in (sc.get("mascot") or {}).get("lines", []):
            bubbles.append({"at": max(0.0, round(ctx.resolve(line.get("t", 0)) - a0, 3)),
                            "text": line["text"], "color": line.get("color", "BLUE")})
        if sc.get("bubble"):
            b = sc["bubble"]
            bubbles.append({"at": max(0.0, round(ctx.resolve(b.get("t", 0)) - a0, 3)),
                            "text": b["text"], "color": b.get("color", "BLUE")})
        # 互动 -> 音频相对秒(at_sent 第 N 句开口时刻)
        inters = []
        game = sc.get("game") or {}
        for it in game.get("interactions", DEFAULT_INTERACTIONS.get(sc["id"], [])):
            it = dict(it)
            n = int(it.pop("at_sent", 1))
            sents = tm.get("sents") or []
            at = (sents[min(n - 1, len(sents) - 1)] - a0) if sents else 0.0
            it["at"] = max(0.0, round(at, 3))
            it["sent_start"] = it["at"]          # 答错回跳点
            # 重听锚点:上一句开口时刻(互动卡在第 N 句句首,讲解在前一句里)
            rp = (sents[max(0, min(n, len(sents)) - 2)] - a0) if sents else 0.0
            it["replay_from"] = max(0.0, round(rp, 3))
            inters.append(it)
        scenes_out.append({
            "id": sc["id"], "template": sc["template"],
            "accent": sc.get("accent", "BLUE"),
            "idx": sc.get("idx", ""), "title": sc.get("title", ""),
            "tag": sc.get("tag", ""), "subtitle": sc.get("subtitle", ""),
            "audio": audio_rel, "dur": tm["dur"],
            "bubbles": sorted(bubbles, key=lambda b: b["at"]),
            "interactions": sorted(inters, key=lambda i: i["at"]),
            "xp": sc.get("xp", 0), "combo": sc.get("combo", ""),
            "final": bool(sc.get("final")),
            "rows": [{**r, "plain": tex_plain(r.get("tex", ""))} for r in sc.get("rows", [])],
            "cta": sc.get("cta", ""),
        })

    data = {"meta": sb.get("meta", {}), "math": _math_constants(), "scenes": scenes_out}
    with open(os.path.join(outdir, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.GAME_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n")
    tpl = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "game", "_template", "index.html")
    shutil.copy(tpl, os.path.join(outdir, "index.html"))
    n_int = sum(len(s["interactions"]) for s in scenes_out)
    print(f"游戏已导出: {outdir}/index.html ({n_int} 个互动点)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--builddir", required=True)
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()
    name = os.path.splitext(os.path.basename(args.storyboard))[0]
    export(args.storyboard, args.builddir, args.outdir or os.path.join("game", name))


if __name__ == "__main__":
    main()
