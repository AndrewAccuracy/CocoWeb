# Prompt 记录

## Prompt 1：确定安全改动方向

```text
背景说明：
当前项目是一个基于 NumPy 的轻量 Transformer / Causal LM，实现了 tokenizer、model、multi-head attention、feed-forward、layernorm 和生成逻辑。

目标：
检查模型推理入口的输入处理问题，重点关注 token id 边界、输入长度、异常响应和生成时的资源消耗控制。

记录内容：
1. 完成代码修改；
2. 增加可运行的测试；
3. 补充 docs/risk-analysis.md、docs/constraint-doc.md、docs/prompt-records.md、docs/security-checklist.md、docs/fix-report.md；
4. 补充 reports/scan-report.md 和 reports/before-after-diff.md；
5. 新增 期末报告_楚柏纶.md，记录本次工作。
```

## Prompt 2：实现输入安全校验

```text
请为 Causal LM 推理入口增加输入安全校验。

风险背景：
当前 model.py 中的 forward(input_ids) 直接执行 self.embeddings[input_ids]。如果 input_ids 中包含负数、超出 vocab_size 的 id、非整数或超长序列，模型会出现非预期行为、底层异常或不必要的资源消耗。generate(input_ids, max_new_tokens) 也没有限制生成长度，可能让总上下文长度超过 max_position_embeddings。

实现要求：
1. 新增独立的输入校验模块；
2. forward() 在索引 embedding 前必须调用校验逻辑；
3. generate() 在循环生成前必须校验初始输入和 max_new_tokens；
4. input_ids 必须是 list 或 tuple；
5. input_ids 不能为空；
6. token id 必须是整数，不能接受 bool、str、float；
7. token id 必须满足 0 <= token_id < vocab_size；
8. 输入长度不能超过 max_position_embeddings；
9. max_new_tokens 必须是非负整数；
10. 生成后的总长度不能超过 max_position_embeddings；
11. 异常输入统一抛出 InputValidationError。

实现要求补充：
1. 校验逻辑需要进入实际执行路径，不能只写在注释里；
2. 超长输入直接返回校验错误，不自动截断；
3. 负数 token 不能继续作为 Python 下标使用。
```

## Prompt 3：审查和整改

```text
请对刚才的代码改动做安全审查。

重点检查：
1. forward() 和 generate() 是否都进入了校验逻辑；
2. 校验是否发生在 embedding 索引和生成循环之前；
3. 负数 token 是否被拒绝，而不是被 Python 当作反向索引使用；
4. 超出 vocab_size 的 token 是否被拒绝；
5. 非整数、空输入、超长输入是否被拒绝；
6. max_new_tokens 是否受剩余上下文长度限制；
7. 测试是否覆盖了正常路径和异常路径。

如果发现遗漏，请记录问题、修改方式和验证结果，并写入 docs/fix-report.md 与 reports/before-after-diff.md。
```
