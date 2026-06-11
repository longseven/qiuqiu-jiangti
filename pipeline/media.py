# -*- coding: utf-8 -*-
"""ffmpeg / 音频时长 封装。

ffmpeg 优先用 PATH 里的,缺失则回退 imageio-ffmpeg 自带的静态二进制
(无 ffprobe,时长测量依次尝试 ffprobe -> macOS afinfo -> 解析 ffmpeg -i)。
"""
import re
import shutil
import subprocess


def ffmpeg_exe():
    p = shutil.which("ffmpeg")
    if p:
        return p
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def audio_duration(path):
    """秒。三级回退:ffprobe / afinfo / ffmpeg -i。"""
    probe = shutil.which("ffprobe")
    if probe:
        out = subprocess.check_output(
            [probe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path])
        return float(out.strip())
    afinfo = shutil.which("afinfo")
    if afinfo:
        out = subprocess.check_output([afinfo, path], text=True)
        m = re.search(r"estimated duration:\s*([\d.]+)\s*sec", out)
        if m:
            return float(m.group(1))
    out = subprocess.run([ffmpeg_exe(), "-i", path], capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", out.stderr)
    if not m:
        raise RuntimeError(f"无法测量音频时长: {path}")
    hh, mm, ss = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return hh * 3600 + mm * 60 + ss


def mix_segments(segs, total, out_path, bitrate="160k"):
    """按起点拼接配音段:segs = [(start_sec, mp3_path), ...] -> m4a。"""
    inputs, filters = [], []
    for i, (st, p) in enumerate(segs):
        inputs += ["-i", p]
        ms = int(round(st * 1000))
        filters.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(segs)))
    mix += f"amix=inputs={len(segs)}:normalize=0:dropout_transition=0[mix]"
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", *inputs,
           "-filter_complex", ";".join(filters) + ";" + mix,
           "-map", "[mix]", "-t", f"{total:.3f}", "-c:a", "aac", "-b:a", bitrate, out_path]
    subprocess.run(cmd, check=True)
    return out_path


def encode_video(frames_pattern, fps, out_path, audio=None, crf=18, preset="medium"):
    """帧序列(+可选配音)-> mp4。不加 -shortest:配音略短于画面属正常。"""
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error",
           "-framerate", str(fps), "-i", frames_pattern]
    if audio:
        cmd += ["-i", audio, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "160k"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf),
            "-preset", preset, out_path]
    subprocess.run(cmd, check=True)
    return out_path
