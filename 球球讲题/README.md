# 球球讲题 · 趣味闯关版讲题视频

竖屏 9:16 数学讲题动画（导数压轴题 f(x)=eˣcos3x − a·e³ˣcosx 三问），
游戏闯关风格：关卡转场卡 + 压轴BOSS血条 + 主角球球 + 弹跳/星爆特效，晓伊配音。
成品约 149.5s，2160×3840（2× 高清）。

## 文件结构（依赖自底向上）

| 文件 | 作用 |
|---|---|
| `animate.py` | 基础层：字体/配色/缓动/文字辅助（被所有模块复用） |
| `animate_vertical.py` | 三问的函数图象（切线图 / h(t) 递减图 / g(x) 山谷图） |
| `animate_fun.py` | 游戏 UI 组件：confetti、血条、震屏、标签、大图 |
| `animate_fun_full.py` | 浅色"纸面"主题覆盖 + 完整三问场景（非闯关旧版入口） |
| `mascot.py` | 角色「球球」，14 种表情（happy/cheer/thumbsup/...），单一事实来源 |
| `animate_fun_full2.py` | **主入口**：闯关版时间轴与全部场景（空白背景 + 大字号） |
| `dub_full2.py` | 用 edge-tts（晓伊）合成解说并按场景时间轴拼成 m4a |
| `narration_full2.m4a` | 已合成的配音成品（不想装 edge-tts 可直接用） |
| `角色设定.md` / `口播文案.md` | 角色与文案文档 |

## 环境要求

- Python 3.9+，`pip install matplotlib numpy`
- 重出配音才需要：`pip install edge-tts`（需联网）
- 合成视频需要 `ffmpeg`（PATH 里可用）
- Windows 中文字体：Microsoft YaHei / SimHei（mascot.py 会自动探测）

## 重建步骤

```bash
# 1) 预览单帧（调试用，dpi 100）
python animate_fun_full2.py --at 60 --out qa.png

# 2) 渲染全部帧（3588 帧 → frames_full2/，2× 高清约 10 分钟）
python animate_fun_full2.py --dpi 200

# 3) 编码 + 混入配音（不要加 -shortest，配音比画面略短属正常）
ffmpeg -y -framerate 24 -i frames_full2/f%05d.png -i narration_full2.m4a \
  -map 0:v -map 1:a -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium \
  -c:a aac -b:a 160k out_full2.mp4

# （可选）重新合成配音——会覆盖 narration_full2.m4a
python dub_full2.py
```

## 改动须知

- **时间轴对齐**：`animate_fun_full2.py` 的 `TIMELINE` 场景时长一旦改变，
  必须同步 `dub_full2.py` 里 SEGS 的场景起点（hook 0.5 / part1 8.7 / part2 46.3 / part3 89.7 / summary 137.7）并重跑配音。
- **mathtext 限制**：不支持 `\tfrac`；公式内不能放中文；✓、ˣ 等字符会变方块（用画线或普通文本替代）。
- 改球球只改 `mascot.py`（`draw_mascot(ax, cx, cy, s, expr, t)`），所有视频共用。
