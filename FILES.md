# 文件说明

普通测试者通常不需要修改以下任何 Skill 文件。

## 交付根目录

- `README.md`：第一入口。
- `QUICKSTART.md`：5 分钟开始。
- `INSTALL.md`：真实环境依赖和安装方式。
- `USAGE.md`：用户视角的完整工作流。
- `PROMPT_TEMPLATES.md`：可复制请求模板。
- `TESTING_GUIDE.md`：测试与评价方法。
- `TROUBLESHOOTING.md`：常见问题。
- `LIMITATIONS.md`：已经验证和未验证边界。
- `VERSION.md`、`CHANGELOG.md`：版本与测试者相关变更。

## skill/

- `skill/SKILL.md`：Skill 入口，定义任务、核心运行路径和硬边界。
- `skill/core/`：跨场景的通用导演核心合同。
- `skill/capabilities/`：根据场景按需加载的导演能力。
- `skill/routing/`：Capability 路由合同和确定性 selector wrapper。
- `skill/schemas/`：IR 结构 Schema，不进入模型上下文。
- `skill/scripts/`：Generation Ready Validator，不进入模型上下文。
- `skill/adapters/`：确定性 Seedance Prompt Adapter 和 Segment 边界。
- `skill/_runtime/`：冻结的工具实现，不是业务规则，不进入模型上下文。
- `skill/runtime/`：Runtime profile 和 context trace。
- `skill/candidate_dependency_manifest.json`：Skill 文件依赖、角色、版本、SHA-256 和 model-context 标记。

## examples/

四个短小输入示例。它们展示怎么提问和怎么看输出结构，不是 benchmark、Schema authority 或黄金答案。

## templates/

可直接复制的基本、对白、动作、悬疑、玄幻、修订和 Bug 报告模板。

## scripts/

- `check_environment.py`：只检查环境。
- `verify_package.py`：重算 manifest 和 checksums。
- `smoke_test.py`：测试纯 Python toolchain；不调用 LLM Director 或视频模型。

## config/

环境变量说明和 Runtime 口径。当前没有必需秘密变量。

## manifests/

`delivery_manifest.json` 记录交付来源、状态和环境；`checksums.sha256` 记录包内关键文件哈希。ZIP 自身哈希位于 ZIP 外部 sidecar。
