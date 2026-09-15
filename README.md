# V0.4 剧集分镜生成 Skill — Tester Release

## 这是什么

本包将剧本文本和用户明确要求转换为结构化 Storyboard IR，并通过确定性 Adapter 输出可用于 Seedance 2.0 的逐镜提示词。它负责剧本理解、镜头设计、景别、机位、构图、人物动作、对白和连续性表达。Seedance 视频生成服务、账号和凭据不包含在本包中。

## 当前状态

这是 Release Candidate / Tester Build：

- `PRODUCTION_CANDIDATE_STRUCTURALLY_VALIDATED`
- `DEPENDENCY_CLOSURE_PASS`
- `REAL_VIDEO_EVALUATION_SKIPPED`

结构、Generation Ready 校验、确定性 Prompt 表达、回归和独立执行依赖已经验证。真实 Seedance 视频质量仍需测试者自行验证；本包不是 `PRODUCTION_READY`。

## 主要能力

- 普通与多人对白
- 动作与位移
- 情绪表演
- suspense / reveal
- establishing / transition
- spatial continuity
- audio transition
- 条件启用的高风险镜头能力

这些是当前可路由能力，不代表全部题材和全部场景均已完成同等级真实视频验证。

## 最快开始

1. 安装 Python 3.10 或更高版本。
2. 解压 ZIP，并在解压目录打开终端。
3. 运行 `python scripts/check_environment.py`。
4. 运行 `python scripts/verify_package.py`。
5. 让支持 Skill 的 Agent 读取 [skill/SKILL.md](skill/SKILL.md)，或把 `skill/` 作为一个独立 Skill 安装。
6. 复制 [最简单模板](templates/basic-storyboard-request.md)，粘贴自己的短剧本。
7. 检查 Storyboard IR 是否达到 Generation Ready，再取得 Seedance Prompt。
8. 在外部 Seedance 服务中测试 Prompt，并按 [Bug 模板](templates/bug-report-template.md)反馈。

详细步骤见 [QUICKSTART.md](QUICKSTART.md)。

## 目录概览

- `skill/`：完整、自包含的 Storyboard Skill。
- `examples/`：四个短小使用示例，不是黄金答案。
- `templates/`：可直接复制的请求和 Bug 模板。
- `scripts/`：环境、完整性和 toolchain smoke test。
- `config/`：环境说明。
- `manifests/`：交付清单与 checksums。

## 安全与隐私

本包不包含任何 API key、个人凭据、真实用户剧本或视频生成服务配置。不要把密钥、个人隐私或未脱敏素材写入 Bug 报告。

## 已知限制

见 [LIMITATIONS.md](LIMITATIONS.md)。

## 如何反馈

复制 [templates/bug-report-template.md](templates/bug-report-template.md)。请提供可复现的剧本、用户要求、IR、Prompt、错误日志和问题分层；不要提供任何密钥或隐私凭据。
