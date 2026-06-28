# 项目约束文档

## 功能目标

为 Causal LM 推理入口增加输入安全校验。重点不是提升模型效果，而是让模型在接收异常输入时有明确边界。

具体目标：

- `forward(input_ids)` 在索引 embedding 前检查输入。
- `generate(input_ids, max_new_tokens)` 在循环生成前检查初始输入和生成长度。
- token id 必须是整数，不能是字符串、布尔值或其他类型。
- token id 必须大于等于 0，并且小于 `vocab_size`。
- 输入长度不能超过 `max_position_embeddings`。
- `max_new_tokens` 不能为负数，也不能让总长度超过上下文上限。
- 异常输入使用统一的 `InputValidationError`，不要依赖 NumPy 抛出的底层异常。

## 实现约束

- 校验逻辑放在实际代码路径中，不能只写在注释里。
- 异常输入不继续运行模型。
- 负数 token 不作为合法输入处理。
- 超长输入直接返回校验错误，不自动截断。

## 审查口径

检查代码时按下面几条看：

1. 安全逻辑是否在 `forward()` 和 `generate()` 的执行路径上。
2. 负数 token、超出词表 token、空输入、非整数输入是否会被拒绝。
3. 输入长度和生成长度是否都受 `max_position_embeddings` 约束。
4. 测试是否覆盖正常输入和异常输入。
5. 文档是否说明了原问题、修改方式和验证结果。
