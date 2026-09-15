# 5 分钟快速开始

## 1. 解压

解压 `storyboard-skill-v0.4-tester.zip`。目录名称可以更改，但请保留包内 `skill/`、`scripts/` 等相对结构。

## 2. 检查 Python

需要 Python 3.10+。在解压目录运行：

```powershell
python --version
python scripts/check_environment.py
python scripts/verify_package.py
```

macOS/Linux 使用相同命令；如果系统将 Python 3 命名为 `python3`，请把上面的 `python` 换成 `python3`。

## 3. 加载 Skill

本包没有虚构的“生成分镜 CLI”。导演生成需要支持 Skill 的 Agent/LLM：

- 临时测试：让 Agent 明确读取本包的 `skill/SKILL.md`，并只按路由加载必要 capability。
- Codex 本地 Skill：将 `skill/` 整体复制或改名到你的 Skill 目录，使 `SKILL.md` 位于该 Skill 根目录；然后调用 `$ai-series-storyboard-seedance-candidate`。

不要把 `examples/` 或 `templates/` 当成业务规则加载。

## 4. 提交最小请求

复制 [templates/basic-storyboard-request.md](templates/basic-storyboard-request.md)，把占位剧本替换成自己的 5–20 秒短场景。

要求 Agent 输出：

1. Generation Ready Storyboard IR。
2. 对应的 Seedance 2.0 Prompt。
3. 如果信息不足，明确指出真正阻塞导演决策的问题，不自行补剧情。

## 5. 检查结果

- required beats 是否完整。
- 对白和 speaker 是否正确。
- Shot 顺序、动作结果、reveal 和连续性是否成立。
- Generation Ready validator 是否 PASS。
- Seedance Prompt 是否与 IR 一致。

## 6. 运行工具链 smoke test

```powershell
python scripts/smoke_test.py
```

这只验证 Router、Validator、Adapter 和 Runtime trace。它不会调用 LLM Director，也不会生成视频。

## 7. 外部生成视频

把最终 Prompt 复制到你有权使用的 Seedance 服务。本包不包含 Seedance API、账号、凭据或视频生成 endpoint。

遇到问题时使用 [Bug 模板](templates/bug-report-template.md)。
