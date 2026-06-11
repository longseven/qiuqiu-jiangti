# -*- coding: utf-8 -*-
"""一键编排:lint -> dub(audio-first)-> 并行渲染 -> ffmpeg 合成。

改任意一句台词后,重跑同一条命令即可全片自动重对齐重渲染。

CLI:
  python -m pipeline.build storyboards/xxx.json                 # 成品 2x 高清
  python -m pipeline.build storyboards/xxx.json --proof         # 低清样片(dpi100/6fps)
  python -m pipeline.build storyboards/xxx.json --mock          # 离线:估时不配音
  python -m pipeline.build storyboards/xxx.json --frames-only   # 只出帧不编码
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

from . import dub as dub_mod
from . import lint as lint_mod
from .media import encode_video

_ENG = None
_FIG = None
_OPTS = None


def _worker_init(sb_path, tl_path, dpi, frames_dir, fps):
    global _ENG, _FIG, _OPTS
    import matplotlib.pyplot as plt
    from . import engine as engine_mod
    _ENG = engine_mod.load(sb_path, tl_path)
    _FIG = plt.figure(figsize=(engine_mod.W, engine_mod.H), dpi=dpi)
    _OPTS = (frames_dir, fps)


def _render_range(rng):
    from .core import C
    a, b = rng
    frames_dir, fps = _OPTS
    for i in range(a, b):
        _ENG.render_frame(_FIG, i / fps)
        _FIG.savefig(os.path.join(frames_dir, f"f{i:05d}.png"), facecolor=C.BG)
    return b - a


def render_frames(sb_path, tl_path, total, fps, dpi, frames_dir, workers=None):
    os.makedirs(frames_dir, exist_ok=True)
    n = int(total * fps)
    workers = workers or max(1, (os.cpu_count() or 4) - 1)
    chunk = max(1, (n + workers * 4 - 1) // (workers * 4))   # 每 worker 约 4 块,均衡负载
    ranges = [(i, min(i + chunk, n)) for i in range(0, n, chunk)]
    t0 = time.time()
    print(f"渲染 {n} 帧 ({total:.1f}s @ {fps}fps, dpi {dpi}, {workers} workers)")
    ctx = mp.get_context("spawn")
    with ctx.Pool(workers, _worker_init, (sb_path, tl_path, dpi, frames_dir, fps)) as pool:
        done = 0
        for c in pool.imap_unordered(_render_range, ranges):
            done += c
            print(f"  {done}/{n} 帧 ({time.time() - t0:.0f}s)", flush=True)
    print(f"帧渲染完成,用时 {time.time() - t0:.0f}s")
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--outdir", default=None, help="默认 build/<storyboard 名>")
    ap.add_argument("--proof", action="store_true", help="低清样片:dpi100 + 6fps + 快编码")
    ap.add_argument("--mock", action="store_true", help="不调 TTS,字数估时(离线调试)")
    ap.add_argument("--dpi", type=int, default=None)
    ap.add_argument("--fps", type=int, default=None)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--frames-only", action="store_true")
    ap.add_argument("--skip-dub", action="store_true", help="复用已有 timeline.json")
    args = ap.parse_args()

    name = os.path.splitext(os.path.basename(args.storyboard))[0]
    outdir = args.outdir or os.path.join("build", name)
    os.makedirs(outdir, exist_ok=True)
    with open(args.storyboard, encoding="utf-8") as f:
        sb = json.load(f)

    # ---- 1) lint(渲染正确性硬门槛)----
    rep = lint_mod.lint(sb)
    for w in rep.warnings:
        print(f"WARN  {w}")
    if not rep.ok:
        for e in rep.errors:
            print(f"ERROR {e}")
        print("lint 未通过,已打回(不进渲染)")
        sys.exit(1)
    print("lint OK")

    # ---- 2) dub:audio-first 时间轴 ----
    tl_path = os.path.join(outdir, "timeline.json")
    narration = os.path.join(outdir, "narration.m4a")
    if args.skip_dub and os.path.exists(tl_path):
        with open(tl_path, encoding="utf-8") as f:
            timeline = json.load(f)
        print(f"复用 {tl_path} (total {timeline['total']}s)")
    else:
        timeline, narration = dub_mod.build_timeline(sb, outdir, mock=args.mock)
    if not os.path.exists(narration or ""):
        narration = None

    # ---- 2.5) SFX 音效轨(numpy 合成,与配音混合)----
    from . import sfx as sfx_mod
    events = sfx_mod.collect_events(sb, timeline)
    if events:
        sfx_wav = os.path.join(outdir, "sfx.wav")
        sfx_mod.render_track(events, timeline["total"], sfx_wav)
        print(f"SFX: {len(events)} 个音效事件")
        if narration:
            from .media import mix_audio
            narration = mix_audio(narration, sfx_wav, os.path.join(outdir, "narration_sfx.m4a"),
                                  timeline["total"])
        else:
            narration = sfx_wav

    # ---- 3) 并行渲染 ----
    fps = args.fps or (6 if args.proof else timeline.get("fps", 24))
    dpi = args.dpi or (100 if args.proof else 200)
    frames_dir = os.path.join(outdir, "frames_proof" if args.proof else "frames")
    render_frames(args.storyboard, tl_path, timeline["total"], fps, dpi, frames_dir,
                  workers=args.workers)
    if args.frames_only:
        return

    # ---- 4) 合成 ----
    suffix = "_proof" if args.proof else ""
    out = os.path.join(outdir, f"{name}{suffix}.mp4")
    encode_video(os.path.join(frames_dir, "f%05d.png"), fps, out, audio=narration,
                 crf=28 if args.proof else 18,
                 preset="veryfast" if args.proof else "medium")
    print(f"成片: {out}" + ("" if narration else "  (无配音)"))


if __name__ == "__main__":
    main()
