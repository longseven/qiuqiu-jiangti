# -*- coding: utf-8 -*-
"""audio-first 配音器:逐场景 TTS -> 实测时长 -> timeline.json + narration.m4a。

对齐方向与旧版相反:不再"画面定时长、配音去凑",而是
  场景时长 = clamp(lead + 台词实测时长 + tail, min_dur, max_dur)
台词改一个字,重跑本模块即全片自动重对齐。

TTS 结果按 (文本+voice+rate+pitch) 哈希缓存,只重合成改动过的场景。
edge-tts 的 WordBoundary 事件被换算成"句锚点"(sents,场景内秒),
storyboard 里的 "@sent:N" 即对齐到第 N 句台词的开口时刻。

CLI:
  python -m pipeline.dub storyboards/xxx.json --outdir build/xxx
  python -m pipeline.dub storyboards/xxx.json --outdir build/xxx --mock   # 离线估时
"""
import argparse
import asyncio
import hashlib
import json
import os
import re

from .media import audio_duration, mix_segments

LEAD = 0.2          # 场景开始 -> 开口
TAIL = 0.5          # 说完 -> 场景结束(呼吸间隙)
MOCK_CPS = 6.0      # mock 模式:中文 +18% 语速约每秒 6 字

_SENT_SPLIT = re.compile(r"[。!?!?]")
_STRIP = re.compile(r"[\s,。!?!?、;;::,.\"'“”‘’()()\-—…·]+")


def split_sentences(text):
    """按句末标点切句(。!?),返回非空句子列表。"""
    parts = [p.strip() for p in _SENT_SPLIT.split(text)]
    return [p for p in parts if p]


def _norm(s):
    return _STRIP.sub("", s)


def sentence_starts(text, boundaries):
    """把 WordBoundary 流映射为每句的起始秒(相对音频开头)。

    boundaries = [(offset_sec, word_text), ...]
    做法:把 boundary 文本按出现顺序拼接,与去标点的台词做字符位置匹配,
    每句的首字符落进哪个 boundary,该 boundary 的 offset 即句起点。
    返回 (starts, coverage):coverage = boundary 覆盖台词字符的比例,
    低于 0.9 时调用方应告警(锚点可能错位)。
    """
    sents = split_sentences(text)
    if not sents or not boundaries:
        return [], 0.0
    total_chars = sum(len(_norm(s)) for s in sents) or 1
    starts_chars = []
    acc = 0
    for s in sents:
        starts_chars.append(acc)
        acc += len(_norm(s))
    spans = []       # (char_lo, char_hi, offset)
    pos = 0
    for off, w in boundaries:
        n = len(_norm(w))
        if n == 0:
            continue
        spans.append((pos, pos + n, off))
        pos += n
    coverage = min(1.0, pos / total_chars)
    last_t = spans[-1][2] if spans else 0.0
    result = []
    for c0 in starts_chars:
        hit = next((off for lo, hi, off in spans if lo <= c0 < hi), None)
        if hit is None:
            # boundary 不完整时按字符比例插值,而非笼统回退到最后时刻
            hit = last_t * (c0 / total_chars) if pos < total_chars else last_t
        result.append(round(hit, 3))
    return result, round(coverage, 3)


def mock_measure(text):
    """离线估时:总时长按字数,句锚点按字数比例。"""
    sents = split_sentences(text)
    n_chars = sum(len(_norm(s)) for s in sents) or 1
    dur = max(1.0, n_chars / MOCK_CPS)
    starts, acc = [], 0
    for s in sents:
        starts.append(round(acc / n_chars * dur, 3))
        acc += len(_norm(s))
    return dur, starts


async def _synth_once(text, voice, rate, pitch, mp3_path):
    import edge_tts
    # 显式要 WordBoundary(7.x 默认 SentenceBoundary):配合本地切句规则,
    # 保证 "@sent:N" 的语义与 lint 校验的句数一致。
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch,
                                boundary="WordBoundary")
    boundaries = []
    tmp = mp3_path + ".part"
    with open(tmp, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                boundaries.append((chunk["offset"] / 1e7, chunk.get("text", "")))
    os.replace(tmp, mp3_path)                       # 成功才落盘,不留半截文件
    return boundaries


async def synth(text, voice, rate, pitch, mp3_path, retries=5, attempt_timeout=90):
    """合成一段;返回 (audio_dur, sent_starts)。

    服务偶发连接重置/悬挂:每次尝试套 wait_for 看门狗,指数退避重试。
    """
    last_err = None
    for attempt in range(retries):
        try:
            boundaries = await asyncio.wait_for(
                _synth_once(text, voice, rate, pitch, mp3_path),
                timeout=attempt_timeout)
            dur = audio_duration(mp3_path)
            sents, coverage = sentence_starts(text, boundaries)
            return dur, sents, coverage
        except Exception as e:                      # 网络抖动/重置/超时
            last_err = e
            await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"TTS 合成失败(已重试 {retries} 次): {last_err}")


def seg_key(text, voice, rate, pitch):
    return hashlib.sha1(f"{voice}|{rate}|{pitch}|{text}".encode()).hexdigest()[:10]


def build_timeline(storyboard, outdir, mock=False, verbose=True):
    """主流程:逐场景测时 -> timeline.json(+ narration.m4a,非 mock)。"""
    meta = storyboard.get("meta", {})
    voice = meta.get("voice", "zh-CN-XiaoyiNeural")
    rate = meta.get("rate", "+18%")
    pitch = meta.get("pitch", "+20Hz")
    audio_dir = os.path.join(outdir, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    rows = []          # (scene, audio_dur, sents_rel_audio, mp3 | None)
    warnings = []
    for sc in storyboard["scenes"]:
        text = str(sc.get("narration") or "").strip()   # 容错非字符串(lint 也会拦)
        if not text:
            rows.append((sc, 0.0, [], None))
            continue
        if mock:
            dur, sents = mock_measure(text)
            rows.append((sc, dur, sents, None))
            continue
        key = seg_key(text, voice, rate, pitch)
        mp3 = os.path.join(audio_dir, f"{sc['id']}-{key}.mp3")
        sidecar = mp3 + ".json"
        if os.path.exists(mp3) and os.path.exists(sidecar):
            with open(sidecar, encoding="utf-8") as f:
                d = json.load(f)
            rows.append((sc, d["dur"], d["sents"], mp3))
            if verbose:
                print(f"  [cache] {sc['id']}: {d['dur']:.2f}s")
            continue
        dur, sents, coverage = asyncio.run(synth(text, voice, rate, pitch, mp3))
        if coverage < 0.9:
            warnings.append(f"场景 {sc['id']}: WordBoundary 覆盖率仅 {coverage:.0%},"
                            f"@sent 锚点可能错位,请人工核对")
        with open(sidecar, "w", encoding="utf-8") as f:
            json.dump({"dur": dur, "sents": sents, "coverage": coverage}, f)
        rows.append((sc, dur, sents, mp3))
        if verbose:
            print(f"  [tts]   {sc['id']}: {dur:.2f}s ({len(text)} 字, {len(sents)} 句, "
                  f"锚点覆盖 {coverage:.0%})")

    scenes_tl, segs, t = [], [], 0.0
    for sc, adur, sents, mp3 in rows:
        min_d = float(sc.get("min_dur", 2.5))
        max_d = float(sc.get("max_dur", max(min_d, 60.0)))
        if adur > 0:
            need = LEAD + adur + TAIL
            dur = max(need, min_d)
            if dur > max_d:
                warnings.append(
                    f"场景 {sc['id']}: 台词 {adur:.1f}s 超出 max_dur {max_d}s,"
                    f"已截到 {max_d}s——请拆段或精简台词")
                dur = max_d
        else:
            dur = min_d
        # 截断时丢弃落在场景外的句锚点,避免 @sent 解析出 > dur 的时刻
        sents_in = [round(LEAD + s, 3) for s in sents if LEAD + s <= dur - 0.2]
        if len(sents_in) < len(sents):
            warnings.append(f"场景 {sc['id']}: {len(sents) - len(sents_in)} 个句锚点"
                            f"超出截断后时长,已移除(引用它们的 @sent 会落到最后一句)")
        scenes_tl.append({
            "id": sc["id"], "start": round(t, 3), "dur": round(dur, 3),
            "audio_start": LEAD if adur > 0 else 0.0,
            "audio_dur": round(adur, 3),
            "sents": sents_in,                              # 场景内秒
        })
        if mp3:
            segs.append((t + LEAD, mp3))
        t += dur

    timeline = {"total": round(t, 3),
                "fps": int(meta.get("fps", 24)),
                "mock": bool(mock),
                "warnings": warnings,
                "scenes": scenes_tl}
    os.makedirs(outdir, exist_ok=True)
    tl_path = os.path.join(outdir, "timeline.json")
    with open(tl_path, "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=1)

    narration = None
    if segs and not mock:
        narration = os.path.join(outdir, "narration.m4a")
        mix_segments(segs, t, narration)
    if verbose:
        for w in warnings:
            print(f"  [warn]  {w}")
        print(f"  timeline: {tl_path}  (total {t:.1f}s)"
              + (f"  narration: {narration}" if narration else "  [mock] 无配音"))
    return timeline, narration


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--mock", action="store_true", help="离线估时,不调 TTS")
    args = ap.parse_args()
    with open(args.storyboard, encoding="utf-8") as f:
        sb = json.load(f)
    build_timeline(sb, args.outdir, mock=args.mock)


if __name__ == "__main__":
    main()
