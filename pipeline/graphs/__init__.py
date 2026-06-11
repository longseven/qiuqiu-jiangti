# -*- coding: utf-8 -*-
"""题型图象插件注册表。

每个插件:  fn(gax, lt, dur, params)
  gax    : 已创建好的 matplotlib axes(布局由场景模板决定)
  lt     : 场景内已过秒数(插件内的子动画节拍自行换算,可用 lt/dur 取相对进度)
  dur    : 场景总时长(秒)
  params : storyboard 里 graph.params 原样传入

插件不感知时间轴与场景编排;新题型 = 新增一个模块,LLM 只能引用插件并填参数。
storyboard 里用 "模块名.函数名" 引用,如 "derivative.tangent"。
"""
import importlib

_REGISTRY = {}


def resolve(name):
    """'derivative.valley' -> 可调用插件;不存在则 KeyError。"""
    if name in _REGISTRY:
        return _REGISTRY[name]
    if "." not in name:
        raise KeyError(f"插件名须为 '模块.函数' 形式,得到 {name!r}")
    mod_name, fn_name = name.rsplit(".", 1)
    try:
        mod = importlib.import_module(f"{__name__}.{mod_name}")
    except ImportError as e:
        raise KeyError(f"题型插件模块 graphs/{mod_name}.py 不存在: {e}") from e
    fn = getattr(mod, fn_name, None)
    if fn is None or not callable(fn):
        raise KeyError(f"graphs/{mod_name}.py 里没有插件函数 {fn_name!r}")
    _REGISTRY[name] = fn
    return fn


def available():
    """列出已知插件(供 lint 与分镜 prompt 用)。"""
    names = []
    from . import derivative
    for mod in (derivative,):
        for fn_name in getattr(mod, "PLUGINS", []):
            names.append(f"{mod.__name__.rsplit('.', 1)[-1]}.{fn_name}")
    return names
