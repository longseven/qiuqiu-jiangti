# 球球讲题 · 视频生产线

把「一题一工程」的讲题视频代码重构为数据驱动的生产线:**新题 = 写一份
storyboard JSON,不写渲染代码**。设计依据见 [开发方案.md](开发方案.md),
原始单视频源码保留在 [球球讲题/](球球讲题/)(基线,不再改动)。

```
storyboard.json ──► lint(渲染正确性硬门槛)
      │
      ├──► dub(audio-first:逐段 TTS → 实测时长)──► timeline.json + narration.m4a
      │
      └──► engine(场景模板 + 题型插件,多进程逐帧渲染)──► frames/*.png
                                   │
                          ffmpeg 合成 ──► out.mp4
```

## 快速开始

```bash
/usr/bin/python3 -m venv venv
./venv/bin/pip install matplotlib numpy edge-tts imageio-ffmpeg pillow

# 一条命令出片(lint → 配音 → 渲染 → 合成)
./venv/bin/python -m pipeline.build storyboards/daoshu_chuangguan.json --proof   # 低清样片,~1分钟
./venv/bin/python -m pipeline.build storyboards/daoshu_chuangguan.json           # 2× 高清成品

# 改了任意台词/文案后:重跑同一条命令,全片自动重对齐重渲染(TTS 有缓存,只重合成改动段)
```

分步调试:

```bash
./venv/bin/python -m pipeline.lint storyboards/xxx.json                       # 只校验
./venv/bin/python -m pipeline.dub  storyboards/xxx.json --outdir build/xxx    # 只配音(--mock 离线估时)
./venv/bin/python -m pipeline.engine storyboards/xxx.json --at 60 --out qa.png \
    --timeline build/xxx/timeline.json                                        # 单帧 QA
```

## audio-first 时间轴(与旧版相反的对齐方向)

旧版:先拍脑袋定场景时长,再手工对齐 dub 的 SEGS 起点(README 里那条
"必须同步五个锚点"的警告)。现在:

- `场景时长 = clamp(0.2s 开口前导 + 台词实测时长 + 0.5s 呼吸间隙, min_dur, max_dur)`
- 台词超出 `max_dur` 时 dub 给出警告(拆段或精简);
- TTS 按 `(文本+voice+rate+pitch)` 哈希缓存在 `build/<名>/audio/`。

## storyboard 写作要点

一份分镜 = `meta` + `scenes[]`。完整示例见
[storyboards/daoshu_chuangguan.json](storyboards/daoshu_chuangguan.json)。

- **模板** `template ∈ hook / card / part / clear / summary`,决定布局与固定演出;
  内容字段(`title`/`idx`/`accent`/`narration`/`items`/`mascot`/`graph`…)全是数据。
- **时间锚点 `t`**:
  - `0~1` 浮点 = 场景内相对进度(台词变长自动等比顺延);
  - `"@sent:N"` / `"@sent:N+0.5"` = 第 N 句台词的开口时刻(句子按 `。!?` 切分),
    答案揭晓等关键节拍用它,与配音精确同步。
- **颜色**:语义名 `BLUE/GOLD/GREEN/PINK/RED/WHITE/MUTED`(或 `#rrggbb`),
  主题(`meta.theme: paper|navy`)负责具体色值。
- **球球**:`mascot.moods` 表情节拍(14 种表情见 [pipeline/mascot.py](pipeline/mascot.py)),
  `mascot.lines` 对话泡;改角色只改 mascot.py,全系列统一。
- **图象** `graph.plugin`:题型插件,目前有
  `derivative.tangent` / `derivative.h_mono` / `derivative.valley`。
  **插件不交给 LLM 写**,新题型由人开发一次,分镜只引用 + 填参数。
- **BOSS 血条**:`meta.boss: true`,在 `clear` 场景标 `crit: true`,
  血量按 crit 数等分自动掉格。

## mathtext 规则(lint 自动拦截)

| 禁用 | 替代 |
|---|---|
| `\tfrac` | `\frac` 或 `\dfrac` |
| 公式内中文 / `\text{中文}` | 中文移到 `$...$` 外 |
| `✓ ✗ ˣ` 等字符 | 画线组件或普通文本 |
| `\begin{...}` 环境 | 拆成多行单式 |

以上之外,lint 还会把每条文本**离屏试渲染**一遍,mathtext 语法错误在进帧渲染前打回。

## 字体

启动时按降级链探测:YaHei/SimHei(Windows)→ PingFang/Hiragino Sans GB/Heiti
(macOS)→ Noto Sans CJK(Linux/CI),无需手工配置。

## 目录

| 路径 | 作用 |
|---|---|
| `pipeline/` | 生产线包(core/fx/mascot/items/templates/engine/graphs/dub/lint/media/build) |
| `storyboards/` | 分镜 JSON(一题一文件,唯一内容事实源) |
| `build/<名>/` | 产物:audio 缓存、timeline.json、frames、mp4 |
| `tools/render_original.py` | 用原版代码渲染对比帧(P0 验收) |
| `球球讲题/` | 原始代码基线(参考,勿改) |

## 下一阶段(见开发方案)

- **P1** 解三角形题型插件组 + 第二道题零渲染代码改动出片
- **P2** compiler:LLM 起草分镜 + 数学/渲染双硬门槛 + rubric 评分
- **P3** 批量队列 / 封面图 / A-B 钩子变体
