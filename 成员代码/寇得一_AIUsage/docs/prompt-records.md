# Prompt 记录

## 记录说明

本文档记录了在使用 Claude Code 辅助开发 MorningModel 安全模块过程中的关键 Prompt 交互。重点展示安全约束如何进入 AI 交互、AI 生成结果中与安全相关的关键片段、以及发现偏差时的修正过程。

**使用工具：** Claude 网页版（对话式） + Claude Code (CLI)  
**模型：** Claude Sonnet  
**开发时间：** 2026年5-6月

> 截图原件保存在 `docs/screenshots/` 目录下，以下按交互顺序引用。

---

## 对话记录一：动态搜索范围与反馈记忆系统设计（Claude 网页版）

以下交互记录来自与 Claude 网页版的对话，展示了 MorningModel 核心安全模块 `search_memory` 的设计过程。该模块涉及数据存取安全和反馈验证机制。

### 交互 1：动态搜索范围的安全设计

**用户 Prompt：**
> "我最近有一个新的想法，我们的搜索范围我觉得应该是不断更新迭代的，你看看，是不是这么个道理"

（附论文 2605.27366v1.pdf 作为参考）

**AI 回应关键片段：** AI 分析了论文中 `skill lifecycle` 的理念，提出将其落地为 MorningModel 的三层动态策略：
1. **动态扩缩搜索范围** — 根据最近 7 天命中率，高命中源多抓，低命中源少抓
2. **建立"日报记忆"** — 从"避免重复"升级成"经验记忆"，记录哪些源常产出 Top 10
3. **基于反馈做下一轮检索** — 热点主题适度扩张，冷门主题收缩

![动态搜索范围讨论](screenshots/Pasted%20Graphic%201.png)
![三层策略详细说明](screenshots/Pasted%20Graphic%202.png)

**安全约束体现：** AI 在建议中明确提出了来源分层和质量控制的安全考量：
- 来源层：将来源按可信度和 reach 分为四格（官方/论文/博客/个人）
- 欺骗层：不只看文章本身，还要看"这件事有没有被别的可靠来源印证"
- 成稿层：最终需满足"有没有具体数字、有没有明确主体、有没有时间线"等最小发布标准

![来源分层安全设计](screenshots/Pasted%20Graphic%203.png)

### 交互 2：反馈记忆机制的安全控制

**用户 Prompt：**
> "对对，然后其实我们还可以随时反馈，好的信息源给下，坏的拉入黑名单这样的"

**AI 回应关键片段：** AI 设计了带安全控制的反馈系统：
- 黑名单不是绝对死刑，而是四种状态：`trusted`（优先保留）、`watchlist`（可以看但要谨慎）、`deprioritized`（默认降权）、`blocked`（默认不进线选）
- 反馈要作用在来源、主题、故事三个层面，并支持"类型"打标签
- 系统收到反馈后写进长期 `memory`，不是只改当次结果

![反馈状态分级设计](screenshots/Pasted%20Graphic%204.png)
![反馈分层与黑名单安全](screenshots/Pasted%20Graphic%205.png)

**安全约束体现：**
- 不是简单的"留/删"二元操作，而是分级管控，避免误杀有价值来源
- 反馈记录存入 `feedback_memory.json`，与自动统计 `search_memory.json` 分离，确保人工判断不被自动逻辑覆盖

### 交互 3：人工纠偏机制的安全实现

**用户 Prompt：**
> "我想问问现在的人工纠偏是怎么做的"

**AI 回应关键片段：** AI 解释了当前的人工纠偏机制，核心是通过独立的 `feedback_memory.py` 模块实现：
1. 用户通过命令行手动录入反馈（如 `python scripts/record_feedback.py --collection "AI Top 10" --kind source --target techcrunch`）
2. 系统将反馈存入 `history/feedback_memory.json`，记录作用范围、反馈对象、动作、理由、历史
3. 排序时将反馈记忆加入候选排序和抓取预算

![人工纠偏机制说明](screenshots/Pasted%20Graphic%206.png)
![反馈排序与安全集成](screenshots/Pasted%20Graphic%207.png)

**安全约束体现：**
- 人工反馈与自动统计隔离存储
- 反馈支持两类：`source`（来源级）和 `topic`（主题级），动作包括 `trust/watch/deprioritize/block` 和 `prefer/watch/deprioritize/block`
- `block` 会被直接排除在候选之外，但不会删除历史数据

### 交互 4：中文反馈解析与邮件监听的安全设计

**用户 Prompt：**
> "好的，就这么做吧，我觉得可以省一些token，就是我们定一个要求的开头的话术怎样，这样我们可以省一些token"

**AI 回应关键片段：** AI 实现了安全的中文反馈解析和邮件监听：
1. **中文固定开头话术** — 确定了统一前缀 `晨报反馈:` 用于识别反馈邮件
2. **中文反馈解析器** `feedback_parser.py` — 将中文回复解析成结构化反馈动作
3. **邮件监听骨架** `poll_feedback_inbox.py` — 先按邮件主题前缀过滤，再解析正文

![中文反馈解析安全设计](screenshots/Pasted%20Graphic%208.png)

**安全约束体现：**
- 邮件主题必须匹配特定前缀（`Re: MorningModel Feedback`），降低误判率
- 解析器只处理符合固定格式的反馈，非结构化内容不会被错误执行
- 反馈解析后转为标准化动作，系统内部不直接执行中文命令

### 交互 5：代码实现与测试验证

**AI 生成代码后的验证：**

AI 在实现 `search_memory.py` 后，提供了完整的测试命令：

```bash
uv run python -m pytest tests/test_search_memory.py -q
uv run python -m pytest tests/test_integration.py tests/test_llm_summarizer.py tests/test_config.py tests/test_document_generator.py -q
```

测试全部通过，确认新增的动态搜索和反馈记忆功能未引入安全回归。

![代码实现与测试通过](screenshots/Pasted%20Graphic.png)
![邮件监听测试通过](screenshots/Pasted%20Graphic%209.png)

---

## 对话记录二：安全模块开发（Claude Code CLI）

以下交互记录来自使用 Claude Code 开发 MorningModel 安全核心模块的过程。

## Prompt 1：Prompt 注入防御模块设计

### 输入 Prompt

```
我需要为 MorningModel（一个 RSS 新闻聚合 + LLM 摘要系统）设计一个 prompt 注入防御模块。

背景：系统从 41 个外部 RSS 源抓取文章，文章标题和内容会被拼接进 LLM Prompt 进行摘要和排名。
这意味着所有文章内容都是不可信输入。

安全约束：
1. 必须对所有不可信文本进行消毒（移除控制字符、零宽字符）
2. 必须检测常见的 prompt 注入模式（忽略指令、泄露 prompt、伪造角色等）
3. 不可信内容在 Prompt 中必须有明确的边界标记
4. 对安全研究类文章（讨论 prompt injection 的学术文章）应有豁免机制，避免误杀

禁止行为：
- 不要使用简单的关键词黑名单，需要正则模式匹配
- 不要只在注释里写安全逻辑，必须在代码中实际执行
- 不要信任 LLM 的输出，输出也需要验证
```

### AI 生成的关键安全代码片段

AI 生成了 `prompt_security.py`，包含以下核心安全机制：

**1. 文本消毒函数 `sanitize_untrusted_text()`：**
```python
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_ZERO_WIDTH = re.compile(r"[​-‏﻿]")

def sanitize_untrusted_text(text, max_chars=None):
    value = str(text)
    value = _CONTROL_CHARS.sub("", value)        # 移除控制字符
    value = _ZERO_WIDTH.sub("", value)            # 移除零宽字符
    value = value.replace(UNTRUSTED_PREFIX, "..._REDACTED")  # 防止边界伪造
    value = value.replace("```", "'''")           # 防止代码块注入
    # ...截断处理
```

**2. 注入检测 `assess_prompt_injection()`：**
```python
_INJECTION_PATTERNS = [
    # 检测 "ignore/disregard/forget previous instructions" 类指令
    re.compile(r"\b(ignore|disregard|forget|override|bypass)\b.{0,80}\b(previous|above|all|system|...)s?\b", ...),
    # 检测 "reveal/print/dump system prompt/api key" 类泄露指令
    re.compile(r"\b(reveal|print|show|dump|exfiltrate|leak)\b.{0,80}\b(prompt|system|api[_ -]?key|secret|...)s?\b", ...),
    # 检测伪造角色 "you are now ChatGPT/the system"
    re.compile(r"\byou are (now )?(chatgpt|an ai|a language model|the system|...)\b", ...),
    # 检测伪造 XML 标签 <system>, <developer> 等
    re.compile(r"<\s*/?\s*(system|developer|user|assistant|instruction|prompt)\s*>", ...),
]
```

**3. 良性上下文豁免：**
```python
_BENIGN_CONTEXT_HINTS = re.compile(
    r"\b(prompt injection|jailbreak|red team|security research|...)\b", re.IGNORECASE
)
# 如果只匹配了1个注入模式，且文本包含安全研究关键词，则视为良性
if _BENIGN_CONTEXT_HINTS.search(value) and score == 1:
    return InjectionAssessment(False, score, "single security-context mention")
```

### 安全约束落实情况

| 约束要求 | 是否落实 | 实现方式 |
|---------|---------|---------|
| 不可信文本消毒 | 是 | `sanitize_untrusted_text()` 移除控制字符/零宽字符 |
| 注入模式检测 | 是 | 7 个正则模式覆盖主要攻击向量 |
| 边界标记 | 是 | `wrap_untrusted()` 使用 BEGIN/END 标记 |
| 学术文章豁免 | 是 | `_BENIGN_CONTEXT_HINTS` 单次匹配豁免 |
| 输出验证 | 是 | `validate_model_text_output()` 二次检测 |

---

## Prompt 2：LLM 调用安全集成

### 输入 Prompt

```
现在需要在 llm_summarizer.py 中集成 prompt_security.py 的安全机制。

要求：
1. 所有文章标题和内容在构造 Prompt 前必须经过 assess_prompt_injection() 检查
2. 可疑文章必须被排除，不进入 LLM Prompt
3. 使用 secure_messages() 构造 LLM 消息，确保包含安全系统提示
4. 使用 wrap_untrusted() 包裹所有不可信内容
5. LLM 返回的文本必须通过 validate_model_text_output() 验证

禁止：
- 不要跳过任何一层检查
- 不要在 except 块中吞掉安全异常
```

### AI 生成的关键集成代码

**文章选择阶段的注入检测（llm_summarizer.py:150-156）：**
```python
for i, article in enumerate(articles):
    title_check = assess_prompt_injection(article.title)
    summary_check = assess_prompt_injection(article.summary or "")
    if title_check.suspicious or summary_check.suspicious:
        print(f"Warning: Excluding suspicious article: '{article.title}'")
        continue  # 直接跳过可疑文章
```

**摘要生成阶段的双重检查（llm_summarizer.py:439-449）：**
```python
content_check = assess_prompt_injection(article.content or "")
title_check = assess_prompt_injection(article.title)
if content_check.suspicious or title_check.suspicious:
    article.summary = "[Error: Article excluded by prompt-injection safety checks.]"
    return article  # 返回错误标记而非处理可疑内容
```

**模型输出验证（llm_summarizer.py:574）：**
```python
summary_text = validate_model_text_output(response.choices[0].message.content)
# 如果输出看起来像注入指令，validate_model_text_output 会抛出 ValueError
```

---

## Prompt 3：API 密钥安全管理

### 输入 Prompt

```
config.py 中需要安全地管理多个 LLM 提供商的 API 密钥。

安全要求：
1. 密钥只能通过环境变量获取，禁止硬编码
2. 日志中打印密钥时必须脱敏
3. 支持多个提供商（OpenAI、DeepSeek、Gemini）的密钥自动切换
4. 密钥获取失败时应警告而非静默失败
```

### AI 生成的关键安全代码

**环境变量密钥管理（config.py:444-455）：**
```python
def get_secret(env_var_name, config_name):
    if env_var_name is None:
        raise ValueError(f"Environment variable name for {config_name} is not configured.")
    secret = os.getenv(env_var_name)
    if secret is None:
        raise ValueError(f"Environment variable '{env_var_name}' for {config_name} is not set.")
    return secret
```

**日志脱敏（llm_summarizer.py:391-395）：**
```python
def _get_masked_api_key(self):
    if self.settings.api_key:
        return f"{self.settings.api_key[:4]}...{self.settings.api_key[-4:]}"
    return "None"
```

---

## 发现偏差与修正记录

### 偏差1：PDF 大文件未限制

**发现：** 初始版本未对 PDF 文件大小做限制，超大 PDF 经过 base64 编码后可能超出模型 Token 限制，导致请求失败或费用暴增。

**修正：** 添加 `MAX_PDF_BYTES = 290000`（约 290KB）硬限制，超过则回退到文本摘要或返回错误。

### 偏差2：长空白序列未处理

**发现：** 初始的 `sanitize_untrusted_text()` 未处理连续空白字符，攻击者可通过大量空格隐藏注入内容。

**修正：** 添加 `_LONG_WHITESPACE = re.compile(r"[ \t]{3,}")` 将 3 个以上连续空格压缩为单个空格。

### 偏差3：模型输出未验证

**发现：** 初始版本只检查输入，未检查 LLM 输出是否被注入影响。

**修正：** 添加 `validate_model_text_output()` 对输出进行二次注入检测，若可疑则抛出异常。

---

## 对话记录三：安全审查与加固（Claude Code CLI）

以下交互记录来自使用 Claude Code 对 MorningModel 进行整体安全审查和加固的过程。

### 交互 6：整体安全审查

**用户 Prompt：**
> "我认为我们现在需要整体梳理一下安全的问题，因为在这个 prompt injection 提升了，我们不得不对其他的安全方面进行操作检查"

**AI 回应关键片段：** AI 对项目进行了全面安全审查，提出 5 个方向的安全加固建议：

1. **必须加固浏览器直接联网** — Playwright 的 `--no-sandbox` 及 `content_extractor.py` (line 5) 需要限制，LLM 调用需通过 `secure_messages()` 和 `wrap_untrusted()` 保证安全
2. **防止路径注入** — 只读取配置白名单中的 `config.toml`、`collections/`、`history/` 文件，禁止 LLM 通过拼接读取无关文件
3. **密钥保护** — API key、SMTP password、IMAP password 只在最终需要的地方获取，局限化分析和脱敏处理
4. **保障已有的 prompt injection 防线** — 检查 JSON response format、验证 `selected_indices` 和 `include` 的类型
5. **所有新增的动作加白名单** — 邮件只发往配置中的收件人，反馈只允许写入 `history/`

![安全审查建议](screenshots/d1380dfe-d267-46f5-be9b-fca81edc9107.png)

### 交互 7：安全加固实施与测试

**AI 完成的安全加固措施：**

1. **默认不再启动 Chromium `--no-sandbox`** — Playwright 自愿自带沙箱模式，配置 `browser_sandbox`、`allow_private_networks` 开关
2. **URL 安全验证** — 新增 `localhost` 禁止访问，`file://` 协议禁止，仅允许 HTTP/HTTPS，保护 RSS 遍历安全
3. **`requests` 库安全** — 固定方向仅访问不可子链跳转 URL，`meta-refresh` 和子链接默认入同一域名限制
4. **运行测试验证通过** — `uv run python -m pytest` 全部通过，编译检查通过

![安全加固实施与测试](screenshots/a8ed5906-2c8d-4073-a095-999358a79b66.png)

### 交互 8：部署安全调整

**用户 Prompt：**
> "你看这个现在有一个很重要的问题，就是我们似乎推送到 GitHub 上的是可以利用 GitHub 启动的是吗，我们不是部署在 macmini 上的吗，你检查一下"

**AI 回应：** 发现系统存在双重部署（GitHub Actions + mac mini 本地定时器），两套同时运行可能导致重复执行和安全隐患。AI 建议并实施了：
- 移除 `daily_digest.yml` 中的 `schedule` 触发器，仅保留 `workflow_dispatch` 手动触发
- 更新 README 和文档说明，统一为 "mac mini 本地部署为默认，GitHub Actions 手动备用"

![部署安全检查](screenshots/download-6.webp)
![部署方案调整实施](screenshots/download-7.webp)

---

## 对话记录四：动态搜索范围开发全过程（Claude 网页版 webp 截图）

以下 webp 截图完整记录了与 Claude 网页版围绕 MorningModel 核心功能（动态搜索范围、反馈记忆、安全策略）的多轮深度对话。

### 交互 9：论文启发 — 动态搜索范围理念

基于论文 2605.27366v1.pdf 中的 `skill lifecycle` 理念，讨论了将"固定 RSS 抓取"升级为"动态搜索策略"的设计方向。AI 提出三层动态更新机制：检索对象、检索依据、检索上下文都应随任务推进变化。

![论文讨论与动态搜索理念](screenshots/download.webp)

### 交互 10：落地到 better-morning 的三层策略

将论文思想翻译成适合日报产品的版本：动态扩缩搜索范围（根据 7 天命中率调整）、建立日报记忆（从"避免重复"升级为"经验记忆"）、基于反馈做下一轮检索。AI 指出了具体的代码切入点：`rss_fetcher.py`、`llm_summarizer.py`、`document_generator.py`。

![三层策略与代码切入点](screenshots/download-1.webp)
![策略详细说明与工程落地](screenshots/download-2.webp)

### 交互 11：提炼论文核心思想

讨论了论文的底层原则：检索不是固定配置而是动态策略、历史不是归档材料而是下一轮决策依据、反馈不是跑完就丢而是要反过来改写搜索范围、工具调用后要沉淀经验。AI 认为这很适合 `better-morning` 现阶段。

![论文核心思想提炼](screenshots/download-3.webp)

### 交互 12：代码实现与测试通过

AI 按照三层策略实现了代码改动：新增 `search_memory.py`，修改 `llm_summarizer.py` 和 `src/main.py`，增加 `article_utils.py`。本地测试全部通过（+375/-8 行改动，6 个文件）。

![代码实现与测试验证](screenshots/download-4.webp)

### 交互 13：来源分层与安全质量控制

讨论了当搜索范围扩大后的信息质量安全问题。AI 提出三层质量控制：
- **来源层**：按可信度和 reach 分为官方/论文/博客/个人四格
- **欺骗层**：不只看文章本身，还要看是否有可靠来源印证
- **成稿层**：需满足最小发布标准（具体数字、明确主体、时间线等）

（对应 Pasted Graphic 3-5.png 中的截图，已在对话记录一中引用）

### 交互 14：反馈系统安全分级设计

设计了四级反馈状态（`trusted/watchlist/deprioritized/blocked`），反馈记忆存入独立的 `feedback_memory.json`，与自动统计隔离。系统收到反馈后写进长期 memory。

（对应 Pasted Graphic 4-7.png 中的截图，已在对话记录一中引用）

### 交互 15：系统运行验证 — 完整晨报输出

系统成功运行并生成了 2026 年 6 月 21 日的完整晨报，证明安全加固后功能正常：

**AI Top 10 摘要输出：**

![AI + Finance 国际晨报标题与 AI Top 10](screenshots/download-7.webp)
![AI Top 10 续（第4-8条）](screenshots/download-8.webp)
![AI Top 10 续（第9-10条）+ AI Research & Safety Top 10 开始](screenshots/download-9.webp)

**AI Research & Safety Top 10 摘要输出：**

![AI Research & Safety Top 10（第3-7条）](screenshots/download-10.webp)
![AI Research & Safety Top 10（第7-10条）+ Finance Top 10 开始](screenshots/download-11.webp)

**Finance Top 10 摘要输出：**

![Finance Top 10（第1-7条）](screenshots/download-12.webp)
![Finance Top 10（第7-10条）+ Feed 抓取报告 + 人工反馈方式](screenshots/download-13.webp)

**Feed 抓取报告 — 全部 41 个 RSS 源成功：**

![Feed 列表上半部分（AI + Research 源）](screenshots/download-14.webp)
![Feed 列表下半部分（Finance 源）+ 人工反馈命令示例](screenshots/download-15.webp)

**MorningModel GitHub 仓库首页：**

![MorningModel 仓库 README 与项目概览](screenshots/95bf939b-be1a-47fc-addb-a4c19c8440a5.png)

---

## 截图完整索引

| 编号 | 文件名 | 内容 |
|------|--------|------|
| 1 | Pasted Graphic.png | search_memory 代码实现与测试 |
| 2 | Pasted Graphic 1.png | 动态搜索范围讨论（三层策略） |
| 3 | Pasted Graphic 2.png | 代码切入点与工程落地 |
| 4 | Pasted Graphic 3.png | 来源分层安全设计 |
| 5 | Pasted Graphic 4.png | 反馈状态分级（trusted/blocked） |
| 6 | Pasted Graphic 5.png | 反馈分层与记忆库设计 |
| 7 | Pasted Graphic 6.png | 人工纠偏机制说明 |
| 8 | Pasted Graphic 7.png | 反馈排序与安全集成 |
| 9 | Pasted Graphic 8.png | 中文反馈解析安全设计 |
| 10 | Pasted Graphic 9.png | 邮件监听测试通过 |
| 11 | download.webp | 论文启发 — 动态搜索理念 |
| 12 | download-1.webp | 三层策略落地到 better-morning |
| 13 | download-2.webp | 策略详细说明与代码切入点 |
| 14 | download-3.webp | 论文核心思想提炼 |
| 15 | download-4.webp | 代码实现与测试（+375/-8） |
| 16 | download-5.webp | 来源分层质量控制（已合并到其他交互） |
| 17 | download-6.webp | 部署安全检查（GitHub Actions vs mac mini） |
| 18 | download-7.webp | 晨报标题与 AI Top 10 |
| 19 | download-8.webp | AI Top 10 续 |
| 20 | download-9.webp | AI Top 10 + AI Research & Safety |
| 21 | download-10.webp | AI Research & Safety Top 10 |
| 22 | download-11.webp | AI Research & Safety + Finance |
| 23 | download-12.webp | Finance Top 10 |
| 24 | download-13.webp | Finance Top 10 + Feed 报告 |
| 25 | download-14.webp | Feed 列表（AI + Research 源） |
| 26 | download-15.webp | Feed 列表（Finance 源）+ 反馈命令 |
| 27 | d1380dfe....png | 安全审查建议（5 方向） |
| 28 | a8ed5906....png | 安全加固实施与测试通过 |
| 29 | 95bf939b....png | MorningModel GitHub 仓库首页 |
