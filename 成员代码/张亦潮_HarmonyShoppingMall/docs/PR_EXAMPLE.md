# 张亦潮 — 认证模块安全加固 PR（填写示例）

> 以下为已填好的示例，可直接复制至 GitHub PR 描述框使用。

---

## 本次 PR 说明

- **负责的环节：** 整改
- **涉及的模块：** 鸿蒙商城后端认证模块（AuthService / AuthFilter / AuthController / JwtUtil / SecurityPathConfig / TokenRevocationService）
- **关联分支：** `feature/auth-jwt-hardening`

---

## 识别的主要安全风险

1. **明文密码存储兼容（T-I02）**
   - **威胁类型（STRIDE）：** Information Disclosure
   - **原代码位置：** `AuthService.java:43-44`
   - **风险描述：** BCrypt 校验失败后仍允许明文 equals 比对，数据库中明文密码可正常登录，BCrypt 保护失效。
   - **风险等级：** 高

2. **无签名 Token 可伪造（T-S01/T-T01）**
   - **威胁类型（STRIDE）：** Spoofing / Tampering
   - **原代码位置：** `AuthService.java:52`, `AuthFilter.java:25-33`
   - **风险描述：** UUID Token 无密码学签名，无法验证完整性；AuthFilter 仅解析 Token 不拦截未认证请求，访问控制依赖各 Controller 自觉检查。
   - **风险等级：** 高

---

## 安全约束如何进入 AI 交互

### 约束文档

每次 AI 对话前完整粘贴 `docs/constraint-doc.md`（项目级安全基线，含 7 条 Hard Constraints 和 6 项验收标准）。

### 结构化 Prompt 设计

| Prompt 要素 | 本次填写内容 |
|-------------|-------------|
| **背景说明** | Spring Boot 3.x 商城后端，认证模块存在 UUID Token、明文密码回退、Filter 不拦截三类缺陷 |
| **任务范围** | 改造 AuthService/AuthFilter，新增 JwtUtil/SecurityPathConfig/TokenRevocationService |
| **约束条件** | C-01 禁止明文密码；C-03 必须 JWT 签名；3.2 Filter 统一 401 拦截 |
| **禁止行为** | 不得硬编码 Secret；不得仅注释声明安全；不得引入 Spring Security 全栈 |

### 关键 Prompt 摘要

```
【粘贴 docs/constraint-doc.md 全文】

## 任务范围
请生成 JwtUtil、TokenRevocationService，改造 AuthService：
- 删除明文密码比对分支；
- login 返回 HS256 JWT；
- logout 按 jti 加入黑名单。

## 约束条件
- C-01：仅 PasswordEncoder.matches()
- 3.3：logout 必须服务端失效 Token

## 禁止行为
- 不得保留 user_session 表写入逻辑
- 不得在日志中打印 token 或 password
```

完整 4 轮 Prompt 见 `docs/prompt-records.md`。

### 偏差发现与纠正

- **是否发现 AI 偏差：** 是
- **偏差描述：** Prompt #2 初版 logout 未实现 JWT 服务端失效；AuthFilter 未改造为统一拦截
- **纠正方式：** 追加 Prompt #3 补全 TokenRevocationService 和 SecurityPathConfig
- **交互记录位置：** `docs/prompt-records.md` §Prompt #2-#3

---

## 审查发现的问题与处置

### 第一层审查（对照 Prompt 约束）

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 无明文密码比对 | ✅ | AuthService.login() 仅 matches() |
| JWT HS256 签名 | ✅ | JwtUtil.signWith(signingKey()) |
| Filter 统一拦截 | ✅ | 非公开路径无用户 → HTTP 401 |
| logout 服务端失效 | ✅ | TokenRevocationService 黑名单 |

### 第二层审查（人工业务逻辑）

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 最小权限白名单 | ✅ | 白名单不含 /wx/order/**、/wx/cart/** |
| 错误响应不泄露 | ✅ | 登录失败统一 errno=402 |
| HTTPS 传输 | ⏳ | 部署层要求，已文档化 |

### 审查结论

**有条件通过** — P0 代码层风险已全部消除；HTTPS 需生产部署配置；登录速率限制列为后续迭代。

---

## 整改内容摘要

| 原问题 | 整改措施 | 涉及文件 |
|--------|----------|----------|
| 明文密码回退 | 删除 equals 分支 | `AuthService.java` |
| UUID 无签名 Token | 引入 HS256 JWT | `JwtUtil.java`, `JwtProperties.java` |
| Filter 不拦截 | 白名单 + 401 拦截 | `AuthFilter.java`, `SecurityPathConfig.java` |
| logout 无法失效 JWT | jti 黑名单 | `TokenRevocationService.java` |

---

## 验证结果

| 测试项 | 预期 | 实际 | 结论 |
|--------|------|------|------|
| 无 Token 访问 /wx/cart/index | 401 | 401 | ✅ |
| 合法 Bearer Token 访问 | 200 | 200 | ✅ |
| 篡改 Token 末位 | 401 | 401 | ✅ |
| logout 后重放 Token | 401 | 401 | ✅ |
| 公开接口 /wx/home/index | 200 | 200 | ✅ |

详细验证记录见 `reports/verification-report.md`。

---

## 相关过程材料位置

| 文档 | 路径 |
|------|------|
| 风险分析 | `成员代码/张亦潮_HarmonyShoppingMall/docs/risk-analysis.md` |
| 约束文档 | `成员代码/张亦潮_HarmonyShoppingMall/docs/constraint-doc.md` |
| Prompt 记录 | `成员代码/张亦潮_HarmonyShoppingMall/docs/prompt-records.md` |
| 审查清单 | `成员代码/张亦潮_HarmonyShoppingMall/docs/security-checklist.md` |
| 代码审查记录 | `成员代码/张亦潮_HarmonyShoppingMall/docs/code-review-record.md` |
| 整改报告 | `成员代码/张亦潮_HarmonyShoppingMall/docs/fix-report.md` |
| 前后对比 | `成员代码/张亦潮_HarmonyShoppingMall/reports/before-after-diff.md` |
| 验证报告 | `成员代码/张亦潮_HarmonyShoppingMall/reports/verification-report.md` |

---

## 已知限制与后续计划

- HTTPS 为部署层要求，本地开发使用 HTTP，生产需 Nginx SSL 终止
- `x-litemall-token` Header 为前端迁移兼容，升级后应移除
- 登录速率限制（T-D01）列为后续迭代

---

## 提交检查清单

- [x] 代码可编译运行
- [x] 独立分支 `feature/auth-jwt-hardening`
- [x] docs/ 与 reports/ 过程文档已更新
- [x] PR 描述已按模板填写
- [ ] 云平台已提交 PR 链接与 Prompt 截图/文本
