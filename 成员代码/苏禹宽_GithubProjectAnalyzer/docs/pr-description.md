# PR 描述留痕

## 本次PR说明

- 负责的环节：开发 / 整改 / 文档更新
- 涉及的模块：`成员代码/苏禹宽_GithubProjectAnalyzer`
- 具体涉及文件：
  - `webapp.py`
  - `web/static/app.js`
  - `tests/test_job_access_control.py`
  - `docs/risk-analysis.md`
  - `docs/constraint-doc.md`
  - `docs/prompt-records.md`
  - `docs/security-checklist.md`
  - `docs/fix-report.md`
  - `reports/scan-report.md`
  - `reports/before-after-diff.md`
  - `期末报告_苏禹宽.md`

本次 PR 聚焦 GitHub Project Analyzer 的 Web 分析任务访问控制。原系统创建任务后，前端可通过 `job_id` 查询任务状态、读取 SSE 实时日志和下载报告文件。`job_id` 是资源定位标识，不适合作为唯一访问凭据，因此本次补强为每个分析任务增加独立访问令牌，并将授权校验落实到结果查询、实时日志和报告下载三个敏感入口。

## 识别的主要安全风险

1. 未授权读取任务结果与报告产物：原流程中只要知道 `job_id`，就可能访问 `/api/result/<job_id>`、`/api/stream/<job_id>` 和 `/api/download/<job_id>/<fmt>`。如果任务链接、日志片段或截图被转发，第三方可能读取分析结果。
2. 资源标识与访问授权混用：`job_id` 主要用于定位任务，不应同时承担授权凭据职责。缺少独立访问令牌会让接口边界不清晰，也不利于后续做过期、撤销或更细粒度权限控制。

## 安全约束如何进入AI交互

在编写代码前，先将风险分析转化为结构化 Prompt 和项目约束文档，并明确要求 AI 在生成代码时遵守以下安全约束：

- 所有修改只能发生在 `成员代码/苏禹宽_GithubProjectAnalyzer` 内，避免影响其他成员模块。
- 每个 Web 分析任务创建时必须生成独立 `access_token`。
- `job_id` 只用于任务定位，不能作为唯一访问凭据。
- `/api/result/<job_id>`、`/api/stream/<job_id>`、`/api/download/<job_id>/<fmt>` 必须统一校验访问令牌。
- 缺失 token 返回 401，错误 token 返回 403。
- token 必须使用安全随机数生成，不能由时间戳、仓库名、用户名或递增序列拼接。
- token 比较必须使用常量时间比较。
- 前端需要自动携带 token，但不得把任务 token 写入 localStorage。
- 必须新增单元测试证明未授权访问被拒绝、合法访问仍可用。
- 不得记录或提交真实 DeepSeek API Key、GitHub Token 或其他敏感凭据。

上述约束已分别写入：

- `docs/constraint-doc.md`
- `docs/prompt-records.md`
- `期末报告_苏禹宽.md`

其中 `prompt-records.md` 和期末报告使用规范化上交 Prompt，包含背景说明、任务范围、约束条件、禁止行为、测试要求和安全审查要求，避免只保留零散对话。

## 审查发现的问题与处置

审查时按“两层检查”执行：

第一层，对照 Prompt 检查功能是否真正实现。检查结果显示，后端已在任务创建时生成 `access_token`，并通过 `_authorize_job` 将授权校验集中到同一处；三个敏感接口均调用该校验逻辑。前端通过 `state.accessToken` 在当前页面生命周期中携带 token，没有写入 localStorage。

第二层，人工检查认证授权分层、最小权限和错误响应。审查中发现并处理了以下问题：

1. 下载链接需要同步携带 token。增加下载接口授权后，如果 `downloadUrls` 不带 token，合法用户也会被拦截。已在后端生成下载链接时追加当前任务 token。
2. 轮询 URL 已包含 token 后，不能继续简单拼接 `?t=...`。已新增 `withQuery` 函数统一合并查询参数，避免形成错误 URL。
3. 本地 Python 环境中存在第三方 `tests` 包，导致单元测试导入路径被抢占。已新增 `tests/__init__.py`，明确本项目测试包边界。
4. 期末报告初版只引用 Prompt 文档，未在报告正文完整展开关键 Prompt、安全片段和偏差记录。已补充为独立章节，便于直接上交审阅。

验证结果：

```text
python -m compileall webapp.py tests
结果：通过

python -m unittest tests.test_job_access_control -v
结果：4 项测试全部通过
```

## 相关过程材料位置

- 风险分析：`成员代码/苏禹宽_GithubProjectAnalyzer/docs/risk-analysis.md`
- 项目约束：`成员代码/苏禹宽_GithubProjectAnalyzer/docs/constraint-doc.md`
- Prompt 记录：`成员代码/苏禹宽_GithubProjectAnalyzer/docs/prompt-records.md`
- 安全审查清单：`成员代码/苏禹宽_GithubProjectAnalyzer/docs/security-checklist.md`
- 整改说明与验证：`成员代码/苏禹宽_GithubProjectAnalyzer/docs/fix-report.md`
- PR 描述留痕：`成员代码/苏禹宽_GithubProjectAnalyzer/docs/pr-description.md`
- 扫描报告：`成员代码/苏禹宽_GithubProjectAnalyzer/reports/scan-report.md`
- 整改前后对比：`成员代码/苏禹宽_GithubProjectAnalyzer/reports/before-after-diff.md`
- 期末报告：`成员代码/苏禹宽_GithubProjectAnalyzer/期末报告_苏禹宽.md`

