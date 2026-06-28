# MorningModel: AI + Finance 国际晨报系统

MorningModel 是一个 RSS 新闻聚合 + LLM 摘要 + 邮件推送系统，从 41 个外部 RSS 源抓取 AI 行业、AI 研究与安全、全球金融三大领域的高信号文章，通过 LLM 进行评分、筛选和中文摘要，每日生成一封排版精美的晨报邮件。

> 项目改编自 [better-morning](https://github.com/00sapo/better-morning)，独立仓库位于 [AndrewAccuracy/MorningModel](https://github.com/AndrewAccuracy/MorningModel)。

## 系统架构

```
41 RSS Feeds (3 Collections)
    ├── AI Top 10           (TechCrunch, OpenAI News, The Verge, ...)
    ├── AI Research & Safety (arXiv, DeepMind Blog, Alignment Forum, ...)
    └── Finance Top 10      (FT, WSJ, CNBC, MarketWatch, ...)
         │
         ▼
    rss_fetcher.py          ─── 抓取 + 历史去重 + last-digest 时间窗口
         │
         ▼
    search_memory.py        ─── 动态搜索记忆：来源命中率 / 主题热度 / 预算分配
         │
         ▼
    article_utils.py        ─── 文章质量评估：来源可信度 / 投机性检测 / 标题去重
         │
         ▼
    prompt_security.py      ─── Prompt 注入防御：消毒 / 检测 / 边界标记 / 输出验证
         │
         ▼
    llm_summarizer.py       ─── LLM 排名 + 摘要（3 提供商 × 双模型架构）
         │
         ▼
    document_generator.py   ─── 报纸排版 HTML 邮件 + digest 历史管理
         │
         ▼
    Email (8 providers)     ─── Gmail / Outlook / QQ / iCloud / 163 / 126 / Yahoo / Zoho
```

## 核心功能

### 动态搜索记忆

系统不是每天固定抓取，而是根据历史表现动态调整策略：

- 记录每个 RSS 源的命中率（`seen/selected/fetch_success`），高命中源多抓、低命中源降权
- 追踪主题热度，热点主题自动扩张抓取预算
- 保留 exploration 通道，避免来源固化
- 7 天窗口自动清理过期数据

### 文章质量评估

多维度评分体系替代简单的时间排序：

- 40+ 域名分级可信度（Federal Reserve = 5, Medium = 2）
- 投机性内容检测（`reportedly/rumor/might` 降权）
- 低信号内容过滤（`sponsored/promo/tutorial` 排除）
- 高影响力关键词加分（`acquisition/earnings/fed/ipo`）
- 标题相似度去重（Jaccard ≥ 0.72 自动合并）
- 跨源聚类加分（同一事件被多源报道时优先）

### Prompt 注入防御

处理 41 个外部 RSS 源的不可信内容，四层纵深防御：

1. **输入消毒** — 移除控制字符、零宽字符、压缩长空白
2. **注入检测** — 7 个正则模式覆盖主要攻击向量
3. **边界标记** — `BEGIN/END_UNTRUSTED_CONTENT` 隔离不可信数据
4. **输出验证** — 对 LLM 输出进行二次注入检测

### 报纸排版邮件

- Masthead 标题头 + Dateline 日期线
- "今日主线" 一句话跨版块摘要
- 三栏 Top 10 列表，每篇标注 "入选优势"
- 底部 Feed 抓取报告 + 人工反馈指引

### 多 LLM 提供商

通过 LiteLLM 统一调用 3 个提供商：

- **OpenAI** — GPT-4o (reasoner) + GPT-4o-mini (light)
- **DeepSeek** — DeepSeek-Reasoner + DeepSeek-Chat
- **Gemini** — Gemini-2.5-Pro + Gemini-2.5-Flash

环境变量一键切换，自动推断提供商。

## 项目结构

```text
寇得一_AIUsage/
├── README.md
├── config.toml                  # 全局配置
├── pyproject.toml               # Python 项目配置
├── run.sh                       # 运行脚本
├── run_local.py                 # 本地运行入口
├── .env.local.example           # 环境变量模板
├── src/
│   ├── main.py                  # 主入口：集合处理 + 聚合 + 输出
│   └── better_morning/
│       ├── prompt_security.py   # Prompt 注入防御
│       ├── llm_summarizer.py    # LLM 摘要与排名
│       ├── config.py            # 配置与密钥管理
│       ├── search_memory.py     # 动态搜索记忆
│       ├── rss_fetcher.py       # RSS 抓取 + 历史去重
│       ├── content_extractor.py # 内容提取 + 浏览器沙箱
│       ├── document_generator.py# 报纸排版邮件生成
│       └── article_utils.py     # 文章质量评估
├── collections/                 # RSS 源集合配置（3 个 TOML）
├── scripts/                     # 工具脚本（清理、预览、反馈录入）
├── tests/                       # 单元测试（8 个文件）
├── docs/                        # 安全管理过程文档
│   ├── risk-analysis.md
│   ├── constraint-doc.md
│   ├── prompt-records.md
│   ├── security-checklist.md
│   ├── fix-report.md
│   └── screenshots/             # AI 交互截图（28 张）
└── reports/
    ├── scan-report.md
    └── before-after-diff.md
```

## 运行方式

### 环境要求

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) 包管理器

### 快速启动

```bash
# 1. 复制环境变量模板并填入 API 密钥
cp .env.local.example .env.local
# 编辑 .env.local，填入 LLM API Key 和邮箱凭据

# 2. 运行
./run.sh
```

### 本地测试

```bash
uv run python -m pytest tests/ -q
```

### 部署

- **Mac mini 本地部署（默认）** — 通过 `launchd` 定时器每 12 小时检查，`run_if_due.py` 控制执行间隔
- **GitHub Actions（手动备用）** — `workflow_dispatch` 触发，不自动运行

## 安全管理过程文档

详见 `docs/` 和 `reports/` 目录，记录了完整的四步安全管理过程（风险识别 → 安全约束 → 审查检查 → 整改验证），以及项目从旧版本 AIUsage 演进到 MorningModel 的全部改动对比。
