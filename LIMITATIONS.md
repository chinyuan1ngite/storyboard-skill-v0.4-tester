# 已知限制

## 已经验证

- Production Candidate 目录结构。
- Generation Ready 结构和 profile 校验。
- Storyboard IR → Seedance Prompt 的确定性表达。
- 14-case Router / IR / Prompt 回归。
- 42/42 Prompt byte-equivalence，Prompt 总量 31,379 bytes。
- 依赖闭包和独立目录执行。
- Progressive disclosure：普通任务只加载 Core 和必要 capability。
- Adapter、QA、Workflow、Legacy 与项目 benchmark 不进入默认模型上下文。

## 尚未完成同等级真实视频验证

- V0.4 与 V0.3.31 的真实视频质量比较。
- Seedance instruction following。
- lip-sync 和 voice continuity。
- L-cut / J-cut 的真实视频实现。
- reference asset binding。
- multi-shot Generation Segment 的最佳策略。
- 长剧本 Router 和 Scene/Segment 边界。
- cinematic-high-risk 能力的实际视频收益。
- macOS/Linux 的同等级平台验证。

## Segment 状态

`Narrative Scene != Director Shot != Generation Segment` 已作为结构边界验证。

当前 `1 Shot → 1 Segment` 只是 fallback/current implementation，不是已证明最优的通用真理。`N Shots → 1 Segment` 仍保持可替换和开放。

## 解释

这些限制表示相关能力尚未完成与结构测试同等级的真实视频验证，不表示它们必然失败。任何生产切换或通用规则修改都需要独立证据。
