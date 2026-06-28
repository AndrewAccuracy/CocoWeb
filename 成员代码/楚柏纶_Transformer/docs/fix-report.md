# 整改说明与验证记录

## 原问题

原始 `model.py` 中的推理入口比较直接：

```python
x = self.embeddings[input_ids]
```

这在教学示例里很简洁，但安全边界不够清楚。只要调用方传入异常 token，就会把问题交给 NumPy 处理。负数 token 更麻烦，因为它不会一定报错，而是可能访问 embedding 矩阵末尾的行。

`generate()` 也有类似问题。它会把传入的 `input_ids` 转成列表，然后按照 `max_new_tokens` 循环生成，没有先检查总长度是否超过 `max_position_embeddings`。

## 整改方式

本次新增 `security_input.py`，把输入校验集中放在一个小模块中：

- `validate_input_ids()` 检查输入类型、空输入、长度、token 类型和 token 范围。
- `validate_max_new_tokens()` 检查生成数量和剩余上下文长度。
- `InputValidationError` 作为统一异常类型，方便上层调用方识别输入问题。

随后修改 `model.py`：

- `forward()` 在读取 embedding 前调用 `validate_input_ids()`。
- `generate()` 在生成循环前调用 `validate_input_ids()` 和 `validate_max_new_tokens()`。

## 改完应满足的条件

- 正常 token 输入可以继续推理。
- 负数 token 被拒绝。
- 超出词表范围的 token 被拒绝。
- 非整数 token 被拒绝。
- 空输入被拒绝。
- 超过上下文长度的输入被拒绝。
- 生成数量不能让总序列长度超过上下文上限。

## 验证记录

本次新增 `test_security_input.py`。测试覆盖以下情况：

- `test_valid_forward_input`
- `test_rejects_negative_token_id`
- `test_rejects_out_of_vocab_token_id`
- `test_rejects_non_integer_token_id`
- `test_rejects_empty_input`
- `test_rejects_overlong_input`
- `test_rejects_too_many_generated_tokens`
- `test_valid_generation_length`

已运行的验证命令：

```bash
cd 成员代码/楚柏纶_Transformer
PYTHONDONTWRITEBYTECODE=1 python3 test_security_input.py
```

验证结果：8 个测试全部输出 `PASS`。
