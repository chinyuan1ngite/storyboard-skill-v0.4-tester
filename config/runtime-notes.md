# Runtime Notes

## Model-facing context

默认模型上下文只包括：

- `skill/SKILL.md`
- 三个 Core 文件
- Router 选中的必要 capability

Python、Schema、Adapter、QA、Workflow、examples、templates 和 manifests 不进入默认模型上下文。

当前结构回归口径：

- G01：14,375 rule bytes。
- 14-case：14,256–16,279 rule bytes。
- 5–7 loaded model modules。
- Adapter model context：0。

## Toolchain

Router、Validator、Adapter 和 Runtime trace 使用 Python 标准库确定性执行。它们不调用 LLM 或 Seedance endpoint。

## Generation Segment

当前 One Shot = One Segment 是 fallback。不要把它当成真实视频已证明的最佳策略。

## Environment

没有必需环境变量。UTF-8 变量仅用于改善部分终端的中文输出。
