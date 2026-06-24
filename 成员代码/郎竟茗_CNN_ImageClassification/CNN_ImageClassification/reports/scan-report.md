# 扫描与验证报告

## 扫描对象

- `security/secure_image_input.py`
- `security/flask_secure_predict_example.py`
- `tests/test_secure_image_input.py`

## 扫描方式

本次采用人工安全审查与单元测试验证相结合的方式进行扫描。扫描重点为图片上传和 CNN 预测入口中的输入处理、文件类型校验、路径穿越、资源消耗和错误响应问题。

## 扫描规则与结果

| 编号 | 检查项 | 风险等级 | 整改前风险 | 整改后结果 | 证据 |
| --- | --- | --- | --- | --- | --- |
| S1 | 是否限制上传文件类型 | 高 | 可能上传脚本、伪装文件或异常文件 | 已限制为 `jpg/jpeg/png` | `validate_and_open_image` |
| S2 | 是否校验真实图片内容 | 高 | 只看后缀可能被伪造图片绕过 | 已使用文件头检测和 Pillow 解码校验 | `test_rejects_fake_image_content` |
| S3 | 是否存在路径穿越风险 | 高 | 用户文件名可能被拼接进服务器路径 | 已拒绝 `../`、`/`、`\` 等路径片段，且不使用用户文件名落盘 | `test_rejects_path_traversal_filename` |
| S4 | 是否限制上传大小 | 中 | 超大文件可能造成资源消耗 | 已限制最大 5MB | `test_rejects_oversized_declared_body` |
| S5 | 是否限制图片尺寸和像素数量 | 中 | 超大图片可能触发高内存消耗 | 已限制最大 4096x4096 和 10000000 像素 | `MAX_WIDTH`、`MAX_HEIGHT`、`MAX_IMAGE_PIXELS` |
| S6 | 是否泄露内部异常信息 | 中 | 预测异常可能暴露服务器路径、模型路径或堆栈 | 已统一返回安全错误信息 | `test_prediction_hides_internal_errors` |
| S7 | 校验失败后是否停止预测 | 高 | 恶意文件可能继续进入模型流程 | 校验失败抛出 `SecurityValidationError` 并直接返回错误 | `predict_image_safely` |

## 单元测试验证

测试命令：

```bash
python -m unittest tests/test_secure_image_input.py
```

详细扫描脚本：

```bash
python scripts/run_security_scan.py --write-report
```

该脚本会同时执行静态安全检查和单元测试，并将详细输出保存到：

```text
reports/scan-report-output.txt
```

测试结果：

```text
......
----------------------------------------------------------------------
Ran 6 tests in 0.018s

OK
```

覆盖场景：

1. 合法 PNG 图片可以通过。
2. 路径穿越文件名被拒绝。
3. 非法扩展名被拒绝。
4. 伪造图片内容被拒绝。
5. 超大请求被拒绝。
6. 模型异常不会泄露内部信息。

## 扫描结论

本次扫描和验证未发现剩余高风险问题。原有图片上传预测入口相关风险已通过输入校验、真实图片内容校验、资源限制、路径安全控制和统一错误响应进行加固。
