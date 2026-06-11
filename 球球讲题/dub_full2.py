# -*- coding: utf-8 -*-
"""
趣味闯关·完整三问 的晓伊配音,按场景时间轴拼成 narration_full2.m4a。
对齐 animate_fun_full2.py:hook@0 / part1@8.5 / part2@46 / part3@89.5 / summary@137.5。
各段不重叠,且每段裁到能塞进对应关卡时长。

Usage: python dub_full2.py
"""
import argparse
import asyncio
import subprocess

import edge_tts

SEGS = [
    (0.5,  "导数压轴大题,三连闯关!三关三套路,跟着球球一关一关拿下!"),
    (8.7,  "第一关,切线!a 等于 e 的负π,先求导:f 撇 等于 e 的 x 次方 乘 cos3x 减 3sin3x,"
           "再减 e 的负π 乘 e 的 3x 次方 乘 3cosx 减 sinx。x 等于 二分之π 一代:f 二分之π 等于零,"
           "切点就在 x 轴上;f 撇 二分之π 等于 4 倍 e 的二分之π,就是斜率。"
           "点斜式一写,切线就是 y 等于 4 e 的二分之π 乘 括号 x 减二分之π。"),
    (46.3, "第二关,求 a 的范围!f 等于零,移项得 e 的 x 次方 cos3x 等于 a 乘 e 的 3x 次方 cos x。"
           "cos3x 拆成 cos x 乘 二cos2x 减一,约掉 cos x,得 二cos2x 减一 除以 e 的 2x 次方 等于 a。"
           "换元 t 等于 2x,h t 等于 二cos t 减一 除以 e 的 t 次方,单调递减,从一 降到 负 e 的负二分之π。"
           "要没有零点,a 就躲区间外:小于等于 负 e 的负二分之π,或者 大于等于一。"),
    (89.7, "第三关,最难的不等式!a 等于零,f 等于 e 的 x 次方 cos3x。g 等于 2f 加 f 撇,"
           "一步合并成 3 根号2 乘 e 的 x 次方 乘 cos 括号 3x 加四分之π。先看符号:g 小于零,"
           "当且仅当 x 在 十二分之π 到 十二分之五π 之间,小球滚进山谷。关键两步:第一,"
           "e 的 x 次方 把右边放大、图象右偏,等高的 x1 加 x3 大于 二分之π;第二,"
           "x2 满足 g 撇 x2 等于 g x1 小于零,推出 x2 大于 四分之π。两个一加,正好大于 四分之三π,得证!"),
    (137.7, "三关通关!切线、取值范围、不等式,方法全讲清楚了。完整解析关注主页,点赞收藏,下道压轴题见!"),
]
GAP = 0.2
TARGET = 149.5


async def synth_all(voice, rate, pitch):
    for i, (_, text) in enumerate(SEGS):
        await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(f"segff{i}.mp3")
        print(f"  synth segff{i}.mp3  ({len(text)} 字)")


def dur(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "default=noprint_wrappers=1:nokey=1", path])
    return float(out.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="zh-CN-XiaoyiNeural")
    ap.add_argument("--rate", default="+18%")
    ap.add_argument("--pitch", default="+20Hz")
    ap.add_argument("--out", default="narration_full2.m4a")
    args = ap.parse_args()
    print(f"synth via {args.voice} (rate {args.rate}, pitch {args.pitch})")
    asyncio.run(synth_all(args.voice, args.rate, args.pitch))

    starts, prev_end = [], 0.0
    for i, (scene_start, _) in enumerate(SEGS):
        st = max(scene_start, prev_end)
        starts.append(st)
        prev_end = st + dur(f"segff{i}.mp3") + GAP
    for i, st in enumerate(starts):
        print(f"  segff{i}: start={st:6.2f}s dur={dur(f'segff{i}.mp3'):5.2f}s end={st+dur(f'segff{i}.mp3'):6.2f}s")
    print(f"  narration total ≈ {prev_end:.2f}s  (video {TARGET}s)")

    inputs, filters = [], []
    for i, st in enumerate(starts):
        inputs += ["-i", f"segff{i}.mp3"]
        ms = int(round(st * 1000))
        filters.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(SEGS)))
    mix += f"amix=inputs={len(SEGS)}:normalize=0:dropout_transition=0[mix]"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs,
           "-filter_complex", ";".join(filters) + ";" + mix,
           "-map", "[mix]", "-t", f"{TARGET:.3f}", "-c:a", "aac", "-b:a", "160k", args.out]
    subprocess.run(cmd, check=True)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
