# 安全审查清单

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| 是否识别了具体安全风险 | 已完成 | 风险集中在模型输入边界、异常输入和资源消耗 |
| 是否把风险转成了 Prompt 约束 | 已完成 | Prompt 中明确写入 token 范围、长度限制和实际代码校验要求 |
| 是否有实际代码逻辑落实约束 | 已完成 | `model.py` 在 `forward()` 和 `generate()` 中调用校验函数 |
| 是否拒绝负数 token id | 已完成 | `security_input.py` 要求 token id 大于等于 0 |
| 是否拒绝超出词表范围的 token id | 已完成 | token id 必须小于 `vocab_size` |
| 是否拒绝非整数 token id | 已完成 | 字符串、浮点数和布尔值都不会被当作合法 token |
| 是否限制输入序列长度 | 已完成 | 输入长度不得超过 `max_position_embeddings` |
| 是否限制生成长度 | 已完成 | `max_new_tokens` 不能让总长度超过上下文上限 |
| 是否统一异常类型 | 已完成 | 异常输入统一抛出 `InputValidationError` |
| 是否有测试验证 | 已完成 | `test_security_input.py` 覆盖正常输入和多类异常输入 |
| 是否影响原模型结构 | 未发现 | Transformer Block、MHA、FFN 等计算逻辑保持不变 |

## 人工审查结论

这次改动没有改变模型结构，也没有影响正常的矩阵计算流程。安全逻辑放在模型入口处，位置比较靠前，能在异常输入进入 embedding 索引之前拦住问题。

我重点检查了负数 token。原代码里 `self.embeddings[input_ids]` 会接受 Python/NumPy 的负数索引，这一点容易被忽略。现在负数会被直接拒绝，不会再落到 embedding 矩阵上。
