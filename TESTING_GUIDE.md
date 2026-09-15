# Tester 测试指南

不要只问“画面好不好看”。先记录可观察错误，再评价导演实现和视频模型表现。

## A. 剧情忠实

- 是否遗漏 required event。
- 是否新增剧本没有的事实。
- 对白是否逐字保持。
- speaker 是否正确。
- 因果顺序和 reveal 时机是否正确。

剧情新增、关键剧情遗漏、对白改写、speaker 错误和提前 reveal 应标记为严重问题。

## B. 导演逻辑

- 每个 Shot 是否有明确功能。
- 动作是否有起点、过程和结果。
- 人物、道具、位置和方向是否连续。
- 空间关系是否可读。
- 景别是否能读到所需信息或表演。
- Shot 顺序和节奏是否服务剧情。

## C. Prompt 可执行性

- 描述是否清晰、无指代歧义。
- framing、camera、action、dialogue 和 constraint 是否互相一致。
- 是否过长或重复。
- 是否出现 IR 中没有的新增事实。
- 是否漏掉不可改变的事实。

Prompt fidelity PASS 不等于真实视频质量 PASS。

## D. Real Video

如果你实际使用 Seedance，请保存：

- 原始剧本和用户请求。
- Storyboard IR。
- 完整 Prompt。
- 模型名称和可见版本。
- duration、aspect ratio、reference assets、seed（若可见）。
- 所有生成结果、失败和重试，不要只保留最好的一次。

建议检查剧情呈现、主体稳定、动作实现、镜头实现、信息揭示、对白/口型、空间连续和模型误解。

单次生成失败不能自动证明 Skill 规则错误。可能根因包括 Director、IR、Adapter、Segment strategy、模型限制、随机方差或参考素材。

## 建议测试顺序

1. 先用一个 5–10 秒普通对白场景。
2. 再测动作、reveal 或多人场景。
3. 最后测试长剧本、高风险镜头、L/J-cut 或复杂非现实运动。
4. 同一问题至少复现两次，再考虑是否为通用规则问题。

## 反馈

使用 [templates/bug-report-template.md](templates/bug-report-template.md)，明确选择问题层级。不要提供 API key、账号或隐私凭据。
