# AI 交互 Prompt 记录

**工具：** Cursor IDE（集成式 AI 编程助手）  
**记录人员：** 张亦潮  
**模块：** 鸿蒙商城认证模块安全加固  
**记录日期：** 2026-06-27

> 说明：以下 Prompt 为实际交互中使用或等效使用的完整文本。每次新对话均先粘贴 `constraint-doc.md` 全文。

---

## Prompt #1 — 风险识别与整改方案设计

**对话轮次：** 第 1 轮  
**目的：** 在编码前完成威胁建模，明确整改边界

```
【项目约束文档 — 见 docs/constraint-doc.md 全文】

## 背景说明
我负责 CocoWeb 仓库中「张亦潮_HarmonyShoppingMall」模块的安全加固。
该模块为 Spring Boot 商城后端，当前认证实现存在以下已知缺陷：
1. AuthService.login() 使用 UUID 作为会话 Token，存储于 user_session 表，无密码学签名；
2. 密码校验存在 BCrypt 与明文比对的双重逻辑（rawPassword.equals(user.getPassword())）；
3. AuthFilter 仅解析 Token 设置 currentUser，不拦截未认证请求；
4. 登录接口通过 HTTP JSON Body 传输明文密码。

## 任务范围
请基于 STRIDE 威胁模型，针对 AuthService、AuthFilter、AuthController 三个核心类：
1. 识别至少 6 项可验证的安全风险，按高/中/低分级；
2. 对照 OWASP ASVS V2（认证）和 V4（访问控制）条款说明不符合项；
3. 给出优先级排序的整改方案，但不生成代码。

## 约束条件
- 分析必须引用具体类名和方法名；
- 不得泛化为"加强安全意识"等不可验证的建议；
- 整改方案须可在 Spring Boot 3.x 环境落地，不引入 Spring Security 全栈。

## 禁止行为
- 不得跳过 risk-analysis 直接写代码；
- 不得将"使用 HTTPS"作为唯一整改措施而不改代码逻辑。
```

**AI 输出摘要（与安全约束相关的关键片段）：**

> - 识别 T-I02：`AuthService` 第 43-44 行明文密码回退，违反 ASVS V2.2.1  
> - 识别 T-E01/T-E02：`AuthFilter` 不拦截导致访问控制依赖 Controller 自觉判空  
> - 建议方案：JWT(HS256) 替代 UUID + `SecurityPathConfig` 白名单 + Filter 统一 401 拦截

**人工判断：** 输出与代码实际情况一致，采纳为 `docs/risk-analysis.md` 的基础。

---

## Prompt #2 — JWT 鉴权核心实现

**对话轮次：** 第 2 轮  
**目的：** 生成 JWT 工具类与 AuthService 改造代码

```
【项目约束文档 — 见 docs/constraint-doc.md 全文】

## 背景说明
基于 docs/risk-analysis.md 的 P0 整改项，需将认证机制从 UUID 会话 Token 迁移至 JWT。

现有代码结构：
- 包名：com.hmshop.backend
- AuthService.java：login() / getUserByToken() / logout()
- AuthFilter.java：从 x-litemall-token Header 读取 Token
- 响应格式：ApiResponse<T>（errno/errmsg/data）
- 已有 PasswordEncoder Bean（BCryptPasswordEncoder）

## 任务范围
请生成以下文件的完整 Java 代码：
1. config/JwtProperties.java — JWT 配置（secret、expiration、issuer），secret 从配置读取；
2. util/JwtUtil.java — 使用 jjwt 0.12.x 实现 generateToken / parseToken / extractUserId；
3. service/TokenRevocationService.java — 内存黑名单，logout 时按 jti 失效；
4. 改造 service/AuthService.java：
   - 删除明文密码比对分支；
   - login 返回 JWT；
   - getUserByToken 验签解析 JWT 后查库；
   - logout 加入黑名单。

## 约束条件（对应 constraint-doc 编号）
- C-01：仅 PasswordEncoder.matches() 校验密码
- C-03/C-04：JWT 必须 HS256 签名，secret 不得硬编码
- 3.1：Claims 含 sub/username/jti/iat/exp/iss
- 3.3：logout 必须服务端失效 Token

## 禁止行为
- 不得保留 user_session 表写入逻辑
- 不得在日志中打印 token 或 password
- 不得使用已废弃的 jjwt 0.11.x API（如 parseClaimsJws）

## 输出要求
- 给出完整类代码，可直接替换；
- 每个类注明满足了哪些约束编号；
- 列出 pom.xml 需新增的 jjwt 依赖坐标。
```

**AI 输出摘要（关键安全实现片段）：**

```java
// AuthService — 仅 BCrypt 校验，无明文回退
if (!passwordEncoder.matches(rawPassword, user.getPassword())) {
    return ApiResponse.fail(402, "账号或密码错误");
}
String token = jwtUtil.generateToken(user.getId(), user.getUsername());

// JwtUtil — HS256 签名 + issuer 校验
Claims claims = Jwts.parser()
    .verifyWith(signingKey())
    .requireIssuer(jwtProperties.getIssuer())
    .build()
    .parseSignedClaims(token)
    .getPayload();
```

**偏差发现与纠正（Prompt #3 前置）：**

AI 初版未实现 `TokenRevocationService`，logout 仅为空操作。人工审查后追加 Prompt #3 要求补全。

---

## Prompt #3 — 统一鉴权拦截与偏差纠正

**对话轮次：** 第 3 轮  
**目的：** 补全 Filter 拦截逻辑，纠正 logout 和服务端 Token 失效

```
【项目约束文档 — 见 docs/constraint-doc.md 全文】

## 背景说明
Prompt #2 生成的 AuthService 缺少服务端 logout 失效机制；
AuthFilter 仍只做 Token 解析，未对受保护路径返回 401。

## 任务范围
1. 新增 config/SecurityPathConfig.java：
   - 公开路径白名单：/wx/auth/login、/wx/home/**、/wx/goods/** 等；
   - 提供 isPublicPath(uri, method) 方法。
2. 改造 config/AuthFilter.java：
   - 优先从 Authorization: Bearer 提取 Token，兼容 x-litemall-token；
   - 非公开路径且无有效用户时，返回 HTTP 401 + ApiResponse.fail(501, "请登录")；
   - 不继续 filterChain。
3. 改造 controller/AuthController.java 的 logout：
   - 提取 Token 并调用 authService.logout(token)。

## 约束条件
- C-06：鉴权拦截集中在 Filter，不在此 Prompt 中修改各 Controller 的判空逻辑（保留双保险）；
- 3.2：401 响应格式与现有 ApiResponse 一致。

## 禁止行为
- 不得将 /wx/order/** 等敏感路径加入白名单；
- 不得在 Filter 中抛出未捕获异常导致 500 泄露信息。

## 输出要求
- 完整类代码；
- 列出公开路径清单供人工审查；
- 给出 3 条 Postman 验证步骤。
```

**AI 输出摘要：**

> - `SecurityPathConfig` 白名单不含 `/wx/cart/**`、`/wx/order/**`  
> - `AuthFilter.writeUnauthorized()` 返回 JSON 格式 401  
> - 验证步骤：无 Token 访问 cart → 401；合法 Token → 200；篡改 Token → 401

**人工判断：** 公开路径清单已核对，`/wx/ai/chat` 保持公开（原设计允许未登录对话）。采纳。

---

## Prompt #4 — 审查确认与文档生成

**对话轮次：** 第 4 轮  
**目的：** 对照约束文档做生成结果检查，输出审查清单与整改报告

```
【项目约束文档 — 见 docs/constraint-doc.md 全文】

## 任务范围
请对照 constraint-doc.md 第 6 节「验证标准」和第 3 节「必须满足的安全要求」，
对当前已生成的认证模块代码进行逐项审查，输出：
1. security-checklist.md 格式的审查清单（含通过/不通过/备注）；
2. fix-report.md 格式的整改说明（问题→措施→验证结果）；
3. reports/before-after-diff.md 格式的前后行为对比。

## 约束条件
- 每项审查结论须引用具体代码位置（类名+方法名）；
- 不得标记"通过"但未给出验证依据；
- 对无法在本次代码中解决的风险（如 HTTPS 部署），须标注为「部署层要求」并说明验证方式。

## 禁止行为
- 不得遗漏 constraint-doc 6.1-6.6 任一验收项；
- 不得将「保留 x-litemall-token 兼容」描述为安全增强（应标注为迁移兼容）。
```

**AI 输出：** 已整理为 `docs/security-checklist.md`、`docs/fix-report.md`、`reports/before-after-diff.md`。

---

## 交互记录统计

| 轮次 | Prompt 目的 | 是否发现偏差 | 处置 |
|------|-------------|-------------|------|
| #1 | 风险识别 | 否 | 直接采纳 |
| #2 | JWT 核心实现 | 是（logout 未失效） | Prompt #3 纠正 |
| #3 | Filter 统一拦截 | 否 | 直接采纳 |
| #4 | 审查与文档 | 否 | 直接采纳 |

**结论：** 安全约束通过结构化 Prompt 进入 AI 交互；偏差在提交 PR 前已通过追加 Prompt 纠正，符合作业「发现偏差时的交互记录」要求。
