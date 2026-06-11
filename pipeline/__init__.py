# -*- coding: utf-8 -*-
"""球球讲题 · 视频生产线(P0 数据驱动重构)。

模块:
  core      基础层:主题配色 / 字体降级链 / 缓动 / 文本绘制原语
  mascot    角色「球球」(单一事实源,与原版绘制逻辑一致)
  fx        特效动词库:starburst / confetti / pop / bubble / shake / boss_bar ...
  graphs    题型图象插件(graphs.derivative.tangent 等)
  items     storyboard item 渲染动词分发
  templates 五类场景模板:hook / card / part / clear / summary
  engine    渲染引擎:storyboard + timeline -> 帧
  dub       audio-first 配音器:逐段 TTS -> 实测时长 -> timeline.json + narration.m4a
  lint      分镜静态校验:schema + mathtext 禁用清单 + 试渲染
  media     ffmpeg / 时长测量 封装
  build     一键编排:lint -> dub -> 并行渲染 -> 合成
"""
