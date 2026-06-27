# 安全审查清单

**审查对象：** 鸿蒙商城认证模块安全加固  
**审查人员：** 张亦潮  
**审查日期：** 2026-06-27  
**对照基准：** `docs/constraint-doc.md` v1.0 + `docs/risk-analysis.md`

---

## 第一层审查：对照 Prompt 约束（AI 生成结果合规性）

| 编号 | 检查项 | 约束来源 | 审查方法 | 结果 | 证据 |
|------|--------|----------|----------|------|------|
| A-01 | 无明文密码比对逻辑 | C-01 | 静态代码审查 `AuthService.login()` | ✅ 通过 | 仅调用 `passwordEncoder.matches()` |
| A-02 | 无密码/Token/Secret 日志输出 | C-02 | 全局搜索 `log.*password`、`log.*token` | ✅ 通过 | 相关类无日志泄露 |
| A-03 | Token 为 HS256 签名 JWT | C-03, 3.1 | 审查 `JwtUtil.generateToken()` | ✅ 通过 | 使用 `Jwts.builder().signWith(signingKey())` |
| A-04 | JWT Secret 从配置读取 | C-04 | 审查 `JwtProperties` + `application.properties.example` | ✅ 通过 | `hmshop.jwt.secret=${HMshop_JWT_SECRET:...}` |
| A-05 | 安全逻辑在代码中实现而非仅注释 | C-05 | 审查 Filter/Service 实际逻辑 | ✅ 通过 | Filter 有 `writeUnauthorized()` 实现 |
| A-06 | 鉴权拦截集中在 Filter | C-06, 3.2 | 审查 `AuthFilter` + `SecurityPathConfig` | ✅ 通过 | 非公开路径无用户则 401 |
| A-07 | logout 服务端失效 Token | 3.3 | 审查 `TokenRevocationService` | ✅ 通过 | jti 黑名单机制 |
| A-08 | 支持 Bearer Token 传递 | 3.1 | 审查 `AuthFilter.extractToken()` | ✅ 通过 | 优先解析 `Authorization: Bearer` |
| A-09 | 登录错误信息不区分用户名/密码 | 3.5 | 审查 `AuthService.login()` 返回值 | ✅ 通过 | 统一返回 errno=402 |
| A-10 | 未引入 Spring Security 全栈 | 约束 §5 | 审查 `pom.xml` 依赖 | ✅ 通过 | 仅 `spring-security-crypto` + jjwt |

---

## 第二层审查：人工业务逻辑审查

| 编号 | 检查项 | 审查方法 | 结果 | 备注 |
|------|--------|----------|------|------|
| B-01 | 认证与授权分层 | Filter 负责认证，Controller 保留二次判空 | ✅ 通过 | 双保险，降低遗漏风险 |
| B-02 | 最小权限原则 | 公开路径白名单审查 | ✅ 通过 | 仅浏览类接口公开 |
| B-03 | 订单/购物车/地址需登录 | 白名单不含 `/wx/order/**` 等 | ✅ 通过 | — |
| B-04 | AI 对话接口访问策略 | `/wx/ai/chat` 为公开 | ⚠️ 已知限制 | 原设计允许匿名，本次不改动 |
| B-05 | 旧 Token 机制兼容 | 仍接受 `x-litemall-token` | ⚠️ 迁移兼容 | 非安全增强，建议前端迁移后移除 |
| B-06 | HTTPS 传输保护 | 部署配置审查 | ⏳ 部署层 | 代码层已文档化，生产需 Nginx SSL |
| B-07 | 登录暴力破解防护 | 接口速率限制 | ❌ 未实现 | 列为后续迭代（risk-analysis T-D01） |
| B-08 | 数据库明文密码迁移 | 旧用户密码格式 | ⚠️ 需运维 | 明文密码用户将无法登录，需批量 BCrypt 迁移 |

---

## 第三层审查：验收标准执行（constraint-doc §6）

| 编号 | 验收条件 | 验证方式 | 结果 | 执行记录 |
|------|----------|----------|------|----------|
| V-01 | 无明文密码比对 | 代码审查 | ✅ | 见 A-01 |
| V-02 | Token 为可验签 JWT | 登录后 jwt.io 解析 | ✅ | Payload 含 sub/username/jti/exp/iss |
| V-03 | 无 Token 访问 /wx/cart/index → 401 | HTTP 请求测试 | ✅ | 见 verification-report.md |
| V-04 | 篡改 Token → 401 | 修改 JWT 末字符测试 | ✅ | 见 verification-report.md |
| V-05 | 合法 Token 访问受保护接口 → 200 | 携带 Bearer Token 测试 | ✅ | 见 verification-report.md |
| V-06 | logout 后原 Token 失效 | 注销后重放 Token 测试 | ✅ | 见 verification-report.md |

---

## 审查结论

- **P0 风险（T-I02, T-S01, T-E01）：** 已全部整改并通过验证
- **P1 风险（T-I01 HTTPS）：** 已文档化部署要求，待生产环境配置
- **P2 风险（T-D01 速率限制）：** 未纳入本次范围，已记录为后续迭代

**审查人签字：** 张亦潮  
**审查状态：** 通过（附已知限制 B-04/B-05/B-08）
