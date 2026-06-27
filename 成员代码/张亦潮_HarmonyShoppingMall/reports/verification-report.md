# 安全加固验证报告

**模块：** 鸿蒙商城认证模块  
**验证人员：** 张亦潮  
**验证日期：** 2026-06-27  
**验证环境：** 本地 Spring Boot 3.2.5 + MySQL（或 H2 测试库）

---

## 1. 验证工具

- Postman / curl
- [jwt.io](https://jwt.io)（JWT 结构解析）
- 静态代码审查（IDE）

---

## 2. 测试用例与结果

### V-01：登录获取 JWT

**请求：**
```http
POST /wx/auth/login HTTP/1.1
Content-Type: application/json

{"username":"demo","password":"<bcrypt-protected-password>"}
```

**预期：** errno=0，data.token 为 `eyJ` 开头的三段式字符串

**实际：** ✅ 通过 — Token 可在 jwt.io 解析，Payload 含 sub/username/jti/exp/iss

---

### V-02：无 Token 访问受保护接口

**请求：**
```http
GET /wx/cart/index HTTP/1.1
```

**预期：** HTTP 401，`{"errno":501,"errmsg":"请登录","data":null}`

**实际：** ✅ 通过

**整改前对比：** HTTP 200 + errno=501（仅业务层拒绝，非标准 401）

---

### V-03：Bearer Token 访问受保护接口

**请求：**
```http
GET /wx/cart/index HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**预期：** HTTP 200，errno=0，返回购物车数据

**实际：** ✅ 通过

---

### V-04：篡改 Token

**操作：** 将 JWT 最后 3 个字符替换为 `XXX`

**请求：**
```http
GET /wx/cart/index HTTP/1.1
Authorization: Bearer eyJhbG...XXX
```

**预期：** HTTP 401

**实际：** ✅ 通过 — JwtUtil.parseToken() 验签失败

---

### V-05：公开接口无需 Token

**请求：**
```http
GET /wx/home/index HTTP/1.1
```

**预期：** HTTP 200，errno=0

**实际：** ✅ 通过

---

### V-06：logout 后 Token 失效

**步骤：**
1. 登录获取 Token
2. `POST /wx/auth/logout` 携带 Bearer Token
3. 使用同一 Token 访问 `GET /wx/cart/index`

**预期：** 步骤 3 返回 HTTP 401

**实际：** ✅ 通过 — TokenRevocationService 黑名单生效

---

### V-07：明文密码无法登录

**前置：** 数据库用户 password 字段为明文 `"123456"`（非 BCrypt）

**请求：**
```http
POST /wx/auth/login HTTP/1.1
Content-Type: application/json

{"username":"legacy_user","password":"123456"}
```

**预期：** errno=402，"账号或密码错误"

**实际：** ✅ 通过 — 无明文 equals 回退

---

## 3. 验证结论

| 编号 | 验收项 | 结果 |
|------|--------|------|
| V-01 | JWT 格式与 Claims | ✅ |
| V-02 | 无 Token → 401 | ✅ |
| V-03 | 合法 Token → 200 | ✅ |
| V-04 | 篡改 Token → 401 | ✅ |
| V-05 | 公开接口正常 | ✅ |
| V-06 | logout 失效 | ✅ |
| V-07 | 明文密码拒绝 | ✅ |

**总评：** 7/7 通过，满足 constraint-doc.md §6 全部验收标准。

---

## 4. 未覆盖项（部署层）

| 项目 | 原因 | 建议验证方式 |
|------|------|-------------|
| HTTPS 传输 | 本地开发 HTTP 环境 | 生产 Nginx 配置后用 SSL Labs 检测 |
| 登录速率限制 | 未纳入本次范围 | 后续接入 Bucket4j 或网关限流 |

---

## 5. 扫描报告说明

> 本次验证以手工测试 + 静态代码审查为主。如需自动化扫描，可在后续迭代接入 OWASP Dependency-Check 或 SonarQube，扫描结果保存至 `reports/scan-report/` 目录。

**建议命令（可选）：**
```bash
mvn org.owasp:dependency-check-maven:check
# 输出报告至 reports/scan-report/dependency-check-report.html
```
