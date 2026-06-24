# 整改说明与验证记录

## 整改问题

CNN 图片分类项目通常存在以下上传入口风险：

1. 仅按后缀判断上传类型，可能被伪造图片绕过。
2. 直接使用用户文件名保存，可能导致路径穿越或覆盖文件。
3. 不限制文件大小和图片尺寸，可能造成资源消耗型攻击。
4. 预测异常直接返回，可能泄露服务器路径、模型路径或代码结构。

## 整改方式

新增 `security/secure_image_input.py`：

- 通过扩展名 allowlist 限制 `jpg/jpeg/png`。
- 使用 `imghdr` 和 Pillow 解码校验真实图片。
- 设置最大上传大小、最大宽高、最大像素数量。
- 拒绝包含路径片段的文件名。
- 预测异常统一返回安全错误信息。

新增 `security/flask_secure_predict_example.py`：

- 提供 Flask 接入示例，方便替换原上传预测入口。

新增 `tests/test_secure_image_input.py`：

- 对关键安全约束进行单元测试。

## 整改后应满足的条件

1. 非图片内容即使使用 `.png` 后缀也会被拒绝。
2. `../sample.png` 等路径穿越文件名会被拒绝。
3. 超过 5MB 的请求会被拒绝。
4. 模型预测异常不会暴露内部错误细节。
5. 合法 PNG/JPG 图片仍可正常进入模型预测流程。

## 验证记录

验证命令：

```bash
python -m unittest tests/test_secure_image_input.py
```

结果：

```text
Ran 6 tests
OK
```
