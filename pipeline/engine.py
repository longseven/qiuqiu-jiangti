# -*- coding: utf-8 -*-
"""渲染引擎:storyboard + timeline -> 帧。

时间轴来自 dub.py 实测的 timeline.json(audio-first);没有 timeline 时
用各场景 min_dur 合成一个默认时间轴(便于 --at 单帧调试)。

CLI(单帧 QA):
  python -m pipeline.engine storyboards/xxx.json --at 60 --out qa.png
  python -m pipeline.engine storyboards/xxx.json --at 60 --timeline build/xxx/timeline.json
"""
import argparse
import json

import matplotlib.pyplot as plt

from . import fx
from .core import C, clamp, overlay, set_theme
from .items import Ctx
from .templates import TEMPLATES, TEMPLATE_SHAKE

W, H = 10.8, 19.2          # 9:16 竖屏;dpi 100 -> 1080x1920,dpi 200 -> 2160x3840


def default_timeline(storyboard):
    """无配音时按 min_dur 排布(调试用)。"""
    scenes, t = [], 0.0
    for sc in storyboard["scenes"]:
        dur = float(sc.get("min_dur", 5.0))
        scenes.append({"id": sc["id"], "start": round(t, 3), "dur": dur,
                       "audio_start": 0.2, "sents": []})
        t += dur
    return {"total": round(t, 3), "scenes": scenes}


class Engine:
    def __init__(self, storyboard, timeline=None):
        self.sb = storyboard
        self.meta = storyboard.get("meta", {})
        set_theme(self.meta.get("theme", "paper"))
        fx.init_confetti()
        self.tl = timeline or default_timeline(storyboard)
        self.total = self.tl["total"]
        self.scenes = storyboard["scenes"]
        self.timing = {t["id"]: t for t in self.tl["scenes"]}
        by_id = {sc["id"]: sc for sc in self.scenes}
        # BOSS 血条:从带 crit 标记的场景推出暴击时刻(场景起点 + 0.5s)
        self.crits = [self.timing[sc["id"]]["start"] + float(sc.get("crit_at", 0.5))
                      for sc in self.scenes if sc.get("crit")]
        self.boss = bool(self.meta.get("boss")) and bool(self.crits)
        # 校验 storyboard 与 timeline 一致
        for sc in self.scenes:
            if sc["id"] not in self.timing:
                raise KeyError(f"timeline 缺少场景 {sc['id']!r},请重跑 dub")
        del by_id

    def scene_at(self, gt):
        for sc in self.scenes:
            t = self.timing[sc["id"]]
            if gt < t["start"] + t["dur"]:
                return sc, t
        sc = self.scenes[-1]
        return sc, self.timing[sc["id"]]

    def render_frame(self, fig, gt):
        fig.clf()
        fig.patch.set_facecolor(C.BG)
        sc, timing = self.scene_at(gt)
        lt = clamp(gt - timing["start"], 0, timing["dur"])
        dx = dy = 0.0
        shake_spec = sc.get("shake", TEMPLATE_SHAKE.get(sc["template"]))
        if shake_spec:
            dx, dy = fx.shake(lt, *shake_spec)
        ax = overlay(fig, dx, dy)
        ctx = Ctx(sc, timing, lt, gt)
        TEMPLATES[sc["template"]](ctx, fig, ax)
        if self.boss and sc["template"] in ("hook", "part", "clear"):
            fx.boss_bar(ax, gt, self.crits, self.meta.get("boss_label", "压轴BOSS"))


def load(storyboard_path, timeline_path=None):
    with open(storyboard_path, encoding="utf-8") as f:
        sb = json.load(f)
    tl = None
    if timeline_path:
        with open(timeline_path, encoding="utf-8") as f:
            tl = json.load(f)
    return Engine(sb, tl)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--timeline", default=None)
    ap.add_argument("--at", type=float, required=True, help="渲染 t 秒处单帧")
    ap.add_argument("--out", default="qa.png")
    ap.add_argument("--dpi", type=int, default=100)
    args = ap.parse_args()
    eng = load(args.storyboard, args.timeline)
    fig = plt.figure(figsize=(W, H), dpi=args.dpi)
    eng.render_frame(fig, args.at)
    fig.savefig(args.out, facecolor=C.BG)
    print(f"wrote {args.out} at t={args.at} (total {eng.total}s)")


if __name__ == "__main__":
    main()
