# 整改前后对比

## 整改前

`forward()` 直接用外部传入的 `input_ids` 索引 embedding：

```python
x = self.embeddings[input_ids]
```

这会带来几个问题：

- `[-1]` 这类负数 token 可能被当作合法下标使用。
- `[99999]` 这类超出词表范围的 token 会触发底层异常。
- 字符串、浮点数等类型错误没有统一处理。
- 超长输入会直接进入注意力计算。

`generate()` 只按 `max_new_tokens` 循环，没有先判断总长度是否超过上下文上限。

## 整改后

新增 `security_input.py`，并在模型入口调用：

```python
input_ids = validate_input_ids(
    input_ids,
    self.config.vocab_size,
    self.config.max_position_embeddings,
)
```

`generate()` 也会检查生成长度：

```python
max_new_tokens = validate_max_new_tokens(
    max_new_tokens,
    self.config.max_position_embeddings,
    len(ids),
)
```

现在异常输入会在进入矩阵计算前被拒绝。正常输入的返回形状和原来一致。

## 对比结论

这次改动解决的是模型入口的安全边界问题。它没有改变 Transformer 的计算逻辑，但让调用方不能再把明显不合法的 token 序列直接送进 embedding 矩阵。
