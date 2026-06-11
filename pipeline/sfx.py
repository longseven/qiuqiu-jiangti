# -*- coding: utf-8 -*-
"""程序合成音效轨(纯 numpy,无外部素材,保持工具链自包含)。

音效动词:ding(揭晓) whoosh(滑入) coin(XP) tick(倒计时) go(倒计时归零)
        drum(关卡卡) fanfare(通关) boom(BOSS 登场)

事件来源:build 阶段扫描 storyboard + timeline,按 item 类型挂默认音效
(meta.sfx=false 可整体关闭;item 里 "sfx": null 可单独关掉)。
"""
import math
import wave

import numpy as np

SR = 44100


def _env(n, attack=0.005, decay=None):
    """攻击-衰减包络。"""
    decay = decay if decay is not None else n / SR
    t = np.arange(n) / SR
    a = np.minimum(t / max(attack, 1e-4), 1.0)
    d = np.exp(-t / max(decay * 0.4, 1e-3))
    return a * d


def _tone(freq, dur, kind="sine", bend=0.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = freq * (1 + bend * t / max(dur, 1e-6))
    ph = 2 * math.pi * np.cumsum(f) / SR
    if kind == "square":
        return np.sign(np.sin(ph))
    if kind == "tri":
        return 2 / math.pi * np.arcsin(np.sin(ph))
    return np.sin(ph)


def ding():
    """答案揭晓:双频钟声。"""
    n = int(SR * 0.55)
    s = (_tone(880, 0.55) * 0.6 + _tone(1318.5, 0.55) * 0.4) * _env(n, decay=0.5)
    return s * 0.7


def whoosh():
    """滑入:噪声扫频。"""
    n = int(SR * 0.28)
    rng = np.random.default_rng(3)
    noise = rng.standard_normal(n)
    # 简易低通:滑动平均,窗口随时间变小 -> 频率升高
    out = np.zeros(n)
    win0, win1 = 28, 6
    for i in range(n):
        w = int(win0 + (win1 - win0) * i / n)
        out[i] = noise[max(0, i - w):i + 1].mean()
    out /= max(1e-9, np.abs(out).max())
    return out * _env(n, attack=0.04, decay=0.22) * 0.5


def coin():
    """金币:两段上行方波(8-bit 感)。"""
    a = _tone(988, 0.07, "square")
    b = _tone(1319, 0.16, "square")
    s = np.concatenate([a, b])
    return s * _env(len(s), decay=0.16) * 0.30


def tick():
    """倒计时滴答。"""
    n = int(SR * 0.06)
    return _tone(1100, 0.06, "tri") * _env(n, attack=0.002, decay=0.05) * 0.5


def go():
    """倒计时归零。"""
    n = int(SR * 0.25)
    return _tone(1660, 0.25, "tri") * _env(n, decay=0.2) * 0.55


def drum():
    """关卡卡登场:低频鼓 + 噪声拍。"""
    n = int(SR * 0.3)
    body = _tone(150, 0.3, bend=-0.5) * _env(n, decay=0.25)
    rng = np.random.default_rng(5)
    snap = rng.standard_normal(n) * _env(n, attack=0.001, decay=0.03) * 0.4
    return (body + snap) * 0.8


def boom():
    """BOSS 登场:低吼。"""
    n = int(SR * 0.7)
    s = (_tone(70, 0.7, bend=-0.3) + 0.5 * _tone(105, 0.7, bend=-0.3)) * _env(n, attack=0.02, decay=0.65)
    return s * 0.9


def fanfare():
    """通关号角:三连升音。"""
    parts = []
    for f, d in ((784, 0.12), (988, 0.12), (1319, 0.34)):
        n = int(SR * d)
        parts.append((_tone(f, d) + 0.4 * _tone(f * 2, d)) * _env(n, decay=d * 0.9))
    s = np.concatenate(parts)
    return s * 0.55


SFX = {"ding": ding, "whoosh": whoosh, "coin": coin, "tick": tick, "go": go,
       "drum": drum, "fanfare": fanfare, "boom": boom}


# ----------------------------------------------------------------------------- 事件收集
def collect_events(storyboard, timeline):
    """扫描分镜,输出 [(abs_sec, sfx_name), ...]。"""
    if storyboard.get("meta", {}).get("sfx", True) is False:
        return []
    timing = {t["id"]: t for t in timeline["scenes"]}
    ev = []
    from .items import Ctx
    for sc in storyboard["scenes"]:
        tm = timing[sc["id"]]
        start, dur = tm["start"], tm["dur"]
        ctx = Ctx(sc, tm, 0.0, start)
        tpl = sc.get("template")
        if tpl == "card":
            ev += [(start + 0.08, "drum"), (start + 0.12, "whoosh")]
        elif tpl == "clear":
            ev += [(start + 0.15, "fanfare"), (start + 0.65, "coin")]
        elif tpl == "hook":
            ev.append((start + 0.15, "whoosh"))
            if sc.get("boss_intro"):
                ev.append((start + ctx.resolve(sc["boss_intro"].get("t", 0.18)), "boom"))
        for it in sc.get("items", []):
            t0 = start + ctx.resolve(it.get("t"))
            custom = it.get("sfx", "auto")
            if custom is None:
                continue
            if custom != "auto":
                ev.append((t0, custom))
                continue
            if it["type"] == "answer":
                ev.append((t0 + 0.15, "ding"))
            elif it["type"] == "quiz":
                reveal = start + ctx.resolve(it.get("reveal", it.get("t")))
                cd = int(it.get("countdown", 3))
                for k in range(cd):
                    ev.append((reveal - cd + k, "tick"))
                ev += [(reveal, "go"), (reveal + 0.25, "ding")]
    return sorted(ev)


def render_track(events, total, out_wav):
    """事件 -> 单声道 wav。"""
    buf = np.zeros(int(SR * (total + 1.0)), dtype=np.float64)
    for t, name in events:
        if name not in SFX:
            raise KeyError(f"未知音效 {name!r}(可用 {sorted(SFX)})")
        s = SFX[name]()
        i = int(max(0.0, t) * SR)
        j = min(len(buf), i + len(s))
        if i < len(buf):
            buf[i:j] += s[:j - i]
    peak = np.abs(buf).max()
    if peak > 0.95:
        buf *= 0.95 / peak
    pcm = (buf * 32767).astype(np.int16)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out_wav
