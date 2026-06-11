# -*- coding: utf-8 -*-
"""用原版 animate_fun_full2 渲染指定时刻的帧(P0 验收对比用)。

原代码字体链只认 Windows 字体,这里导入后补打 macOS/CI 降级链,
其余逻辑零改动。

Usage:
  ./venv/bin/python tools/render_original.py --at 27.7 --out build/orig_27.7.png
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "球球讲题"))
sys.path.insert(0, ROOT)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pipeline.core import FONT_CHAIN  # noqa: E402  字体降级链(副作用:写 rcParams)

import animate_fun_full2 as F2  # noqa: E402

# animate / mascot 在 import 时按 Windows 字体设置过 rcParams,这里统一覆盖回来
plt.rcParams["font.sans-serif"] = FONT_CHAIN + ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", type=float, required=True, action="append",
                    help="可重复:渲染多个时刻")
    ap.add_argument("--out", action="append", required=True)
    ap.add_argument("--dpi", type=int, default=100)
    args = ap.parse_args()
    assert len(args.at) == len(args.out), "--at 与 --out 数量须一致"
    fig = plt.figure(figsize=(F2.W, F2.H), dpi=args.dpi)
    for t, out in zip(args.at, args.out):
        F2.render_frame(fig, t)
        fig.savefig(out, facecolor=F2.A.BG)
        print(f"wrote {out} at t={t}")


if __name__ == "__main__":
    main()
