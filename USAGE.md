# 使用手册

## 基本工作流

```text
Script + explicit constraints
→ Storyboard Skill
→ Generation Ready Storyboard IR
→ deterministic validation
→ deterministic Seedance Adapter
→ Seedance Prompt
```

LLM/Agent 负责一次导演决策。Validator 只检查结构、状态和明确违规，不重新导演。Adapter 只表达已经完成的 IR，不重新选镜头。

## 推荐输入

尽量提供：

- 剧本文本和事件顺序。
- 人物名称、关系和剧本已声明的状态。
- 场景、时间、空间关系和关键道具。
- 完整对白及 speaker。
- 不可改变的剧情、reveal、身份和连续性要求。
- 可选：目标时长、画幅、渲染风格、角色参考素材。

没有的事实不要强行填写。信息不足时，要求系统指出真正阻塞导演决策的缺口，不要自行补剧情、身份、空间或世界观。

## 输出是什么

### Storyboard IR

模型无关的导演中间结果。它记录 Scene 目标、required beats、Shot、主体、景别、摄影机、动作、对白、空间、时间和连续状态。

### Shot

一个具有明确叙事功能的导演镜头。Shot 不是为了凑镜数，也不等同于一次模型调用。

### Generation Segment

视频模型的一次执行范围。当前工具链使用 One Shot = One Segment 作为 fallback，但这不是已被真实视频证明的最佳策略。

### Seedance Prompt

确定性 Adapter 对 IR 的模型表达。它不应新增剧情、改对白、重排镜头或改变导演决定。

必须记住：

`Narrative Scene != Director Shot != Generation Segment`

## 常见使用方式

### 1. 整段剧本

提供完整剧本，要求先识别 Narrative Scene，再按场景路由能力。长剧本 Router 尚未完成同等级验证，建议分段复核 Scene 边界和跨 Scene 状态。

### 2. 单个 Scene

提供场景前置状态、场景文本和预期结束状态。适合快速测试 Dialogue、Action、Reveal 等能力。

### 3. 修改某个 Shot

粘贴当前 Shot，明确“只修改什么”和“必须保持什么”。不要让系统顺便重写其他 Shot。

### 4. 增加硬约束

把不可变要求写成可验证事实，例如：

- 不得新增角色。
- 不得提前揭示门后人物。
- 第一句对白必须由林然说，逐字保持。
- 角色手中的钥匙跨镜保持。

### 5. 指定风格

区分渲染风格和导演风格。真实、动画、3D、画幅、材质和光影可作为 Adapter style；如果要求会改变镜头数、机位或构图逻辑，应明确交给 Director 决策。

### 6. 玄幻、灵异或非现实动作

提供故事世界规则、能力触发、动作因果和可见结果。可以违反现实物理，但必须在当前世界设定、空间声明和目标生成能力下内部一致。不要让模板自动创造 lore。

### 7. 多人对白

明确人物、打断关系、注意力转移、空间位置和关键反应。检查 speaker、群体关系、轴线和连续状态。

## 修订流程

不推荐直接手改 IR，因为容易破坏 beat、Shot、audio 和 continuity 之间的引用。

不要只说：

> 帮我优化一下。

推荐：

> 只修改镜 3：不要推镜，保持固定机位；门后的角色必须到镜 4 才揭示。保持镜 1、2、4 的对白、动作和顺序不变。

修订后重新运行 Generation Ready validation，再生成 Prompt。

## 工具边界

- `skill/routing/route_candidate.py`：确定性路由，不生成 Storyboard IR。
- `skill/scripts/validate_storyboard_ir.py`：校验已有 Candidate IR。
- `skill/adapters/render_seedance_2.py`：把已有 Candidate IR 渲染为 Prompt。
- `skill/runtime/trace_candidate_runtime.py`：记录规则上下文。

纯 Python 工具不能替代 LLM Director。完整调用示例见 [QUICKSTART.md](QUICKSTART.md)。
