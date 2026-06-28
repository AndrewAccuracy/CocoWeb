# 整改前后对比说明

## 对比概述

本文档对比 MorningModel 项目在安全加固前后的关键差异，展示安全管理措施的实际效果。

---

## 对比 1：Prompt 注入防御（从无到有）

### 整改前（AIUsage 旧版本）

旧版本没有 Prompt 注入防御机制。LLM 客户端直接将用户任务描述传递给 API，无消毒、无检测、无边界标记：

```python
# 旧版 app/llm_client.py
class LLMClient:
    def generate_next_action(self, task, context, history, max_retries=3):
        # 直接调用 API，无安全处理
        return self.api_client.generate_next_action(task, context, history, max_retries)
```

**风险：** 如果 `task` 或 `context` 包含恶意指令，LLM 会直接执行。

### 整改后（MorningModel 新版本）

新增完整的安全模块 `prompt_security.py`，在所有 LLM 调用路径中强制执行：

```python
# 新版 - 三层防护

# 第1层：输入消毒
title_text = sanitize_untrusted_text(article.title, max_chars=300)

# 第2层：注入检测
title_check = assess_prompt_injection(article.title)
if title_check.suspicious:
    continue  # 排除可疑内容

# 第3层：边界标记 + 安全系统提示
safe_content = wrap_untrusted("article content", article.content)
messages = secure_messages(prompt)  # 包含安全系统提示

# 第4层：输出验证
summary_text = validate_model_text_output(response.choices[0].message.content)
```

**效果：** 四层纵深防御，覆盖输入→处理→输出全链路。

---

## 对比 2：API 密钥管理

### 整改前

旧版本通过 YAML 配置文件管理密钥：

```yaml
# 旧版 config/config.yaml.example
openai:
  api_key: "your-api-key-here"   # 需要用户填入真实密钥
  model: "gpt-4"
```

```python
# 旧版 app/llm_client.py
def _load_config(self):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)  # 密钥在配置文件中明文存储
```

**风险：** 用户可能忘记将 `config.yaml` 加入 `.gitignore`，导致密钥提交到 Git。

### 整改后

新版本完全基于环境变量：

```python
# 新版 config.py
def get_secret(env_var_name, config_name):
    secret = os.getenv(env_var_name)
    if secret is None:
        raise ValueError(f"Environment variable '{env_var_name}' is not set.")
    return secret

# 日志脱敏
def _get_masked_api_key(self):
    return f"{self.settings.api_key[:4]}...{self.settings.api_key[-4:]}"
```

**效果：** 密钥不会出现在任何配置文件或日志中。

---

## 对比 3：不可信内容边界

### 整改前

旧版本的上下文收集没有区分可信和不可信内容：

```python
# 旧版 app/context.py
def collect_context():
    # 收集系统上下文，所有数据混在一起
    context = Context(
        system_info=get_system_info(),
        current_directory=os.getcwd(),
        # ...
    )
```

### 整改后

新版本明确区分可信和不可信内容，不可信内容有清晰的边界标记：

```python
# 新版 prompt_security.py
def wrap_untrusted(label, text, max_chars=None):
    safe_text = sanitize_untrusted_text(text, max_chars=max_chars)
    return (
        f'{UNTRUSTED_PREFIX} label="{safe_label}"\n'
        f"{safe_text}\n"
        f"{UNTRUSTED_SUFFIX}"
    )
```

**效果：** LLM 可以清楚地区分系统指令和不可信数据。

---

## 对比 4：错误处理安全性

### 整改前

旧版本在 Approval Gate 拒绝操作时，直接返回包含内部信息的错误：

```python
# 旧版 - 可能泄露内部状态
return {
    "status": "rejected",
    "message": f"用户拒绝了操作: {action.dict()}"  # 暴露完整操作结构
}
```

### 整改后

新版本返回安全的错误标记，不暴露内部细节：

```python
# 新版 - 安全的错误响应
article.summary = "[Error: Article excluded by prompt-injection safety checks.]"
# 不暴露检测模式、匹配细节或内部状态
```

**效果：** 攻击者无法通过错误响应推断安全检测机制的细节。

---

---

## 对比 5：文章筛选策略（从无到多维评分）

### 整改前

旧版本无文章质量评估，所有文章等权处理。

### 整改后

新增 `article_utils.py`，实现多维度文章质量评估：

- **来源可信度**：40+ 域名分 5 级（Federal Reserve/BIS = 5, Medium/Substack = 2）
- **投机性检测**：识别 `reportedly/rumor/might` 等不确定用语，降权
- **低信号过滤**：过滤 `sponsored/promo/tutorial` 等低价值内容
- **高影响力加分**：`acquisition/earnings/fed/ipo` 等关键词加分
- **标题去重**：Jaccard 相似度 ≥ 0.72 自动去重
- **跨源聚类**：同一事件被多源报道时加分

**效果：** 从"抓什么就用什么"进化为"多维质量评分 + 智能排序"。

---

## 对比 6：搜索策略（从固定到动态记忆）

### 整改前

旧版本每次运行独立，不记录历史表现，所有源等权抓取。

### 整改后

新增 `search_memory.py`，实现带经验记忆的动态抓取：

- 记录每个源的命中率（`seen/selected/fetch_success`）
- 高命中源加分 +2.5，低命中源减分 -2.0
- 热门主题自动扩张抓取预算
- 保留 exploration 通道避免来源固化
- 7 天窗口自动清理过期数据

**效果：** 系统会越用越聪明，逐步学会哪些源和主题值得关注。

---

## 对比 7：邮件输出（从纯文本到报纸排版）

### 整改前

旧版本输出纯 Markdown 文本，无排版设计。

### 整改后

完全重写 `document_generator.py`，生成报纸排版的 HTML 邮件：

- Masthead 标题头 + Dateline 日期线
- "今日主线" 一句话跨版块摘要
- 三栏 Top 10 列表（AI / AI Research & Safety / Finance）
- 每篇标注 "入选优势" 说明
- 底部 Feed 抓取报告 + 人工反馈指引
- 支持 8 个邮箱提供商（Gmail/Outlook/QQ/iCloud 等）

**效果：** 从开发者工具升级为可直接交付的产品级晨报。

---

## 对比 8：LLM 集成（从单模型到多提供商双模型）

### 整改前

旧版本仅支持 OpenAI 单一模型。

### 整改后

通过 LiteLLM 支持 3 个提供商（OpenAI / DeepSeek / Gemini），双模型架构：

- **Reasoner model**：用于文章排名和筛选（如 GPT-4o / DeepSeek-Reasoner / Gemini-2.5-Pro）
- **Light model**：用于摘要生成（如 GPT-4o-mini / DeepSeek-Chat / Gemini-2.5-Flash）
- 自动推断提供商，环境变量一键切换
- 支持 thinking effort 配置

**效果：** 灵活选择性价比最优的 LLM 组合。

---

## 整改效果总结

| 维度 | 整改前 | 整改后 |
|------|--------|--------|
| Prompt 注入防御 | 无 | 四层纵深防御 |
| 密钥管理 | YAML 文件明文 | 环境变量 + 日志脱敏 |
| 内容边界 | 可信/不可信混合 | 明确边界标记 |
| 错误响应 | 可能泄露内部信息 | 安全错误标记 |
| 输出验证 | 无 | 二次注入检测 |
| 注入检测模式 | 无 | 7 类正则模式 |
| 文章质量评估 | 无 | 多维评分 + 去重 + 聚类 |
| 搜索策略 | 固定等权 | 动态记忆 + 经验学习 |
| 邮件输出 | 纯 Markdown | 报纸排版 HTML 邮件 |
| LLM 支持 | 单一 OpenAI | 3 提供商 + 双模型架构 |
| 邮箱支持 | 无 | 8 个提供商自动配置 |
| 部署 | 手动运行 | mac mini 定时 + GitHub Actions |
| 测试 | 无 | 8 个测试文件 |
