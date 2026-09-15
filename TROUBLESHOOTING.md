# 故障排查

## Python 找不到

- 症状：`python: command not found` 或“不是内部或外部命令”。
- 可能原因：未安装 Python，或未加入 PATH。
- 检查：运行 `python --version`、`python3 --version` 或 Windows 的 `py --version`。
- 解决：安装 Python 3.10+，然后用系统实际命令替换文档中的 `python`。

## Python 版本过低

- 症状：SyntaxError，或环境检查报告 FAIL。
- 可能原因：Python < 3.10。
- 检查：`python --version`。
- 解决：改用 Python 3.10 或更高版本。

## 文件路径错误

- 症状：找不到 `skill/SKILL.md` 或脚本。
- 可能原因：终端不在包根目录，或只复制了部分文件。
- 检查：当前目录应同时包含 `README.md`、`skill/` 和 `scripts/`。
- 解决：切换到正确目录；不要从 ZIP 中只提取单个脚本。

## ZIP 解压结构错误

- 症状：出现多层重复目录，命令路径不匹配。
- 可能原因：解压工具额外创建了目录。
- 检查：找到第一层同时包含 `README.md` 和 `skill/` 的目录。
- 解决：在该目录运行命令。外层目录名称可以改变。

## Skill 没被加载

- 症状：Agent 没有遵循 Storyboard 输出和路由合同。
- 可能原因：只粘贴了剧本，没有加载 `skill/SKILL.md`。
- 检查：让 Agent 明确说明已读取的 Skill 入口和所选 capability。
- 解决：按 [QUICKSTART.md](QUICKSTART.md) 安装或显式引用 Skill。不要加载 examples 代替 Skill。

## Router 没选预期 Capability

- 症状：路由结果与场景重点不符。
- 可能原因：短文本没有明确动作、群体、reveal、声画或空间线索；当前 Router 对隐含语义和长文覆盖仍有限。
- 检查：运行 Router 并查看 `cue_evidence`、`route_confidence` 和 `uncertainty`。
- 解决：在用户请求中明确场景事实，不要加入不存在的剧情。把可复现样本按 Router 类型反馈。

## IR validation failed

- 症状：Validator 输出 FAIL。
- 可能原因：缺 required 字段、引用不存在的 beat/subject/shot、关键导演值为 unknown，或时间/状态矛盾。
- 检查：逐条读取错误位置。
- 解决：让 Director 修订对应决定后重新生成；不要用无意义默认值填充。

## Prompt renderer failed

- 症状：Adapter 返回 Generation Ready 或音频关联错误。
- 可能原因：IR 尚未通过校验、音频没有 shot_refs，或输入文件命名/目录不匹配。
- 检查：先运行 Validator；确认输入目录包含 `*.candidate.ir.json`。
- 解决：修正 IR，不要让 Adapter 重新导演。

## 中文编码问题

- 症状：终端乱码或 UnicodeDecodeError。
- 可能原因：终端编码不是 UTF-8。
- 检查：运行 `python scripts/check_environment.py`。
- 解决：设置 `PYTHONUTF8=1` 和 `PYTHONIOENCODING=utf-8`，或使用 UTF-8 终端。

## Permission issue

- 症状：PermissionError，无法写输出。
- 可能原因：输出目录只读或被安全软件锁定。
- 检查：尝试在用户可写目录创建普通文本文件。
- 解决：把包和输出放到有权限的位置；不要用管理员权限绕过未知安全问题。

## 改了目录名后无法运行

- 症状：重命名包或 Skill 后找不到内部文件。
- 可能原因：只移动了部分目录，破坏内部相对结构。
- 检查：`skill/` 内仍应包含 SKILL、core、capabilities、_runtime 等。
- 解决：可重命名外层目录或整个 Skill 目录，但不要单独移动其内部文件。

## manifest hash mismatch

- 症状：`verify_package.py` 报 Hash mismatch。
- 可能原因：文件损坏、换行被编辑器改写、包被修改或下载不完整。
- 检查：重新下载并比较 ZIP 外部 SHA-256。
- 解决：使用原始 ZIP 重新解压。不要手工“修正” manifest 来掩盖差异。

## 只拿到了部分目录

- 症状：环境检查或验证报告 missing。
- 可能原因：交付、同步或解压不完整。
- 检查：阅读 [FILES.md](FILES.md)。
- 解决：重新取得完整 ZIP。

## Seedance 生成效果差

- 症状：视频人物漂移、动作失败、口型错误或镜头未执行。
- 可能原因：Director/IR/Prompt 问题，也可能是模型限制、随机性、参考素材或 Segment strategy。
- 检查：先确认 Hard Fidelity，再重复生成并保存 provenance。
- 解决：不要立刻增加全局规则。使用 Bug 模板定位问题层，并注明模型、版本、参数和重复性。
