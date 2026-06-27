# 鸿蒙商城 — AI 辅助开发约束文档

> **用途说明：** 本文档为项目级安全约束基线。每次开启新的 AI 编程对话时，应**完整粘贴**本文档至对话开头，以防止 AI 在长上下文交互中遗忘早期安全要求。

**版本：** v1.0  
**适用范围：** 鸿蒙商城后端（`com.hmshop.backend`）  
**最后更新：** 2026-06-27

---

## 1. 项目背景

- **项目名称：** 鸿蒙商城（HarmonyShoppingMall）
- **技术栈：** Java 17 + Spring Boot 3.x + Spring Data JPA
- **包名：** `com.hmshop.backend`
- **当前任务：** 认证授权模块安全加固（JWT 鉴权、密码存储、统一访问控制）

---

## 2. 绝对禁止行为（Hard Constraints）

AI 生成或修改的代码**不得**包含以下行为：

| 编号 | 禁止项 | 理由 |
|------|--------|------|
| C-01 | 明文存储或明文比对用户密码 | 违反 OWASP ASVS V2.2.1 |
| C-02 | 在日志、异常信息、API 响应中输出密码、JWT Secret 或完整 Token | 信息泄露 |
| C-03 | 使用无签名的随机字符串作为认证 Token | 无法验证完整性 |
| C-04 | 将 JWT Secret 硬编码并提交至版本库 | 密钥泄露 |
| C-05 | 仅在注释中声明"已做安全处理"而不实现对应逻辑 | 虚假安全感 |
| C-06 | 绕过统一鉴权 Filter，在单个 Controller 中重复实现不一致的认证逻辑 | 访问控制遗漏 |
| C-07 | 引入已知 CVE 的高危依赖版本 | 供应链风险 |

---

## 3. 必须满足的安全要求（Mandatory Requirements）

### 3.1 身份认证

- 登录密码校验**仅允许** `PasswordEncoder.matches()`（BCrypt）
- 登录成功后签发 **HS256 签名 JWT**，Claims 包含：`sub`(userId)、`username`、`jti`、`iat`、`exp`、`iss`
- Token 有效期默认 24 小时，可通过配置调整
- 客户端传递 Token 优先使用 `Authorization: Bearer <token>`

### 3.2 访问控制

- 受保护路径（订单、购物车、地址、用户中心等）必须在 `AuthFilter` 层**统一拦截**
- 未认证访问受保护路径返回 HTTP 401 + `{"errno":501,"errmsg":"请登录"}`
- 公开路径（商品浏览、首页、登录接口）白名单集中配置于 `SecurityPathConfig`

### 3.3 会话注销

- 注销时将 JWT 的 `jti` 加入黑名单，直至原 Token 过期
- 不得假设"客户端删除 Token 即等于服务端注销"

### 3.4 传输安全

- 代码层：登录接口不在响应中返回密码
- 部署层：生产环境**必须**通过 HTTPS 传输（Nginx/网关 SSL 终止），本地开发可用 HTTP

### 3.5 错误处理

- 登录失败统一返回"账号或密码错误"，不区分用户名不存在与密码错误
- 不向前端暴露堆栈跟踪或 SQL 细节

---

## 4. 代码风格与工程约束

- 遵循现有包结构与命名风格（`service` / `config` / `controller` / `util`）
- 新增类需有明确单一职责，避免过度抽象
- 不修改与本次安全加固无关的业务逻辑
- 保留现有 `ApiResponse<T>` 响应格式（`errno` / `errmsg` / `data`）

---

## 5. 依赖约束

- JWT 实现使用 `io.jsonwebtoken:jjwt` 0.12.x（Jakarta EE 兼容）
- 不引入 Spring Security 全栈（避免大范围重构），仅使用 `spring-security-crypto` 做密码哈希

---

## 6. 验证标准（Acceptance Criteria）

整改完成的判定条件：

1. `AuthService.login()` 中不存在明文密码比对代码
2. 登录返回的 Token 为三段式 JWT，可通过 [jwt.io](https://jwt.io) 解析并验证签名
3. 不带 Token 访问 `GET /wx/cart/index` 返回 401
4. 篡改 Token 末位字符后访问受保护接口返回 401
5. 携带合法 Token 访问受保护接口正常返回业务数据
6. `logout` 后原 Token 无法继续访问受保护接口

---

## 7. 变更范围边界

**允许修改：**
- `AuthService.java`、`AuthFilter.java`、`AuthController.java`
- 新增 `JwtUtil.java`、`JwtProperties.java`、`SecurityPathConfig.java`、`TokenRevocationService.java`
- `AppConfig.java`、`pom.xml`、`application.properties.example`

**不允许修改：**
- 商品、订单、购物车业务逻辑（除鉴权上下文获取方式外）
- 数据库表结构（`UserSession` 表保留但不再用于认证）

---

## 8. AI 交互协议

每次向 AI 提交任务时，按以下结构组织 Prompt：

```
[粘贴本约束文档全文]

## 本次具体任务
（描述要修改的文件和目标）

## 输出要求
- 给出完整可编译的代码
- 说明每一处改动对应哪条约束编号（如 C-01、3.1）
- 列出需要人工验证的测试用例
```
