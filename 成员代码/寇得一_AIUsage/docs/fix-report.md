# 整改说明与验证记录

## 整改概述

本文档记录了 MorningModel 项目从旧版本（AIUsage macOS 自动化代理）演进到新版本（RSS + LLM 新闻聚合系统）过程中，针对安全问题的整改措施和验证结果。

---

## 整改项 1：新增 Prompt 注入防御模块

### 问题描述

旧版本（AIUsage）的安全重点是 Approval Gate（操作确认闸门），但缺乏对 LLM Prompt 注入的防御。新版本（MorningModel）引入了 41 个外部 RSS 源作为不可信输入，Prompt 注入成为首要安全风险。

### 整改措施

新增 `src/better_morning/prompt_security.py`，实现完整的 Prompt 注入防御：

| 功能 | 实现 |
|------|------|
| 文本消毒 | `sanitize_untrusted_text()` — 移除控制字符、零宽字符、压缩空白 |
| 注入检测 | `assess_prompt_injection()` — 7 个正则模式匹配 |
| 边界标记 | `wrap_untrusted()` — BEGIN/END 标记 + label |
| 安全消息 | `secure_messages()` — 强制包含安全系统提示 |
| 输出验证 | `validate_model_text_output()` — 二次注入检测 |

### 验证方式

1. **单元测试验证：** 针对各类注入 payload 进行测试
2. **代码审查：** 确认所有 LLM 调用路径都经过安全模块处理

### 整改后应满足的条件

- [x] 所有不可信文本在进入 Prompt 前经过消毒
- [x] 所有不可信文本在进入 Prompt 前经过注入检测
- [x] 可疑文章被排除，不进入 LLM Prompt
- [x] LLM 输出经过二次验证

---

## 整改项 2：API 密钥管理安全加固

### 问题描述

旧版本使用 YAML 配置文件管理 API 密钥，虽然提供了 `config_example.yaml` 模板，但存在密钥被提交到 Git 的风险。日志中也未对密钥进行脱敏处理。

### 整改措施

| 措施 | 实现位置 |
|------|---------|
| 环境变量管理 | `config.py:get_secret()` — 从 `os.getenv()` 获取密钥 |
| 提供商自动推断 | `config.py:infer_llm_provider()` — 根据已配置的环境变量自动选择提供商 |
| 日志脱敏 | `llm_summarizer.py:_get_masked_api_key()` — 仅显示前4后4位 |
| .gitignore 保护 | `.env.local` 文件在 `.gitignore` 中，不会被提交 |

### 验证方式

1. `grep -r "sk-" src/` — 确认无硬编码 API 密钥
2. `grep -r "api_key" src/ | grep -v "env\|getenv\|masked\|settings"` — 确认密钥仅通过安全路径访问
3. 检查 Git 历史确认无密钥泄露

### 整改后应满足的条件

- [x] 所有密钥通过环境变量管理
- [x] 日志中密钥已脱敏
- [x] 配置文件中不包含实际密钥

---

## 整改项 3：不可信内容处理增强

### 问题描述

新版本需要处理来自外部 RSS 源的大量不可信内容，包括 HTML 文章、PDF 文件等。需要防止 Token 溢出、超大文件处理失败等问题。

### 整改措施

| 措施 | 实现位置 |
|------|---------|
| Token 截断 | `llm_summarizer.py:_truncate_text_to_token_limit()` |
| PDF 大小限制 | `MAX_PDF_BYTES = 290000`，超过则回退 |
| 内容长度限制 | `sanitize_untrusted_text(max_chars=...)` |
| 摘要长度限制 | `wrap_untrusted('article summary', art.summary, max_chars=3000)` |

### 验证方式

1. 使用超大文本输入测试截断机制
2. 使用超过 290KB 的 PDF 测试回退机制
3. 确认 Token 预算计算正确（预留 25% 给模型响应）

### 整改后应满足的条件

- [x] 超大 PDF 不会导致系统崩溃
- [x] Token 超限时内容被安全截断
- [x] 截断后的内容标记 `[TRUNCATED]`

---

## 整改项 4：模型输出安全验证

### 问题描述

即使输入端做了防护，攻击者仍可能通过精心构造的内容影响 LLM 输出。如果输出中包含被注入的指令性内容，不经验证直接发送给用户，等于将攻击传递到下游。

### 整改措施

新增 `validate_model_text_output()` 函数，对 LLM 生成的文本进行二次注入检测：

```python
def validate_model_text_output(text):
    value = sanitize_untrusted_text(text)
    assessment = assess_prompt_injection(value)
    if assessment.suspicious:
        raise ValueError(f"Model output looks instruction-injected: {assessment.reason}")
    return value
```

### 验证方式

在 `llm_summarizer.py` 中确认所有 LLM 输出路径都经过 `validate_model_text_output()` 处理：
- `summarize_text()` → 第 574 行
- `_summarize_text_content()` → 第 640 行

### 整改后应满足的条件

- [x] 所有 LLM 输出在使用前经过注入检测
- [x] 可疑输出抛出异常而非静默通过

---

## 整改验证总结

| 整改项 | 状态 | 验证方式 |
|--------|------|---------|
| Prompt 注入防御 | 已完成 | 单元测试 + 代码审查 |
| API 密钥安全 | 已完成 | grep 扫描 + Git 历史检查 |
| 不可信内容处理 | 已完成 | 边界值测试 |
| 模型输出验证 | 已完成 | 调用路径追踪 |

**结论：** 所有识别的安全问题均已整改，未引入新的安全问题。
