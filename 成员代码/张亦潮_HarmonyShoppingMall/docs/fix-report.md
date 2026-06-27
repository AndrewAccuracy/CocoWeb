# 整改说明与验证记录

**模块：** 鸿蒙商城认证模块（HarmonyShoppingMall）  
**整改人员：** 张亦潮  
**整改日期：** 2026-06-27  
**关联 PR 分支：** `feature/auth-jwt-hardening`（建议）

---

## 1. 整改总览

| 原问题编号 | 问题描述 | 整改措施 | 涉及文件 | 验证状态 |
|------------|----------|----------|----------|----------|
| T-I02 | 明文密码比对回退 | 删除 equals 分支，强制 BCrypt | `AuthService.java` | ✅ 已验证 |
| T-S01/T-T01 | UUID Token 无签名 | 引入 HS256 JWT | `JwtUtil.java`, `JwtProperties.java` | ✅ 已验证 |
| T-E01/T-E02 | 鉴权不统一，可绕过 | Filter 统一拦截 + 路径白名单 | `AuthFilter.java`, `SecurityPathConfig.java` | ✅ 已验证 |
| T-S02 | 非标准 Token 传递 | 支持 Authorization: Bearer | `AuthFilter.java` | ✅ 已验证 |
| — | logout 无法失效 JWT | jti 内存黑名单 | `TokenRevocationService.java` | ✅ 已验证 |
| T-I01 | 明文传输密码 | 部署层 HTTPS 要求 | `application.properties.example` | ⏳ 部署待配置 |

---

## 2. 逐项整改说明

### 2.1 问题：明文密码存储兼容（T-I02）

**原代码：**
```java
boolean passwordOk = passwordEncoder.matches(rawPassword, user.getPassword()) ||
        rawPassword.equals(user.getPassword());
```

**问题分析：** 第二分支允许数据库中存储明文密码并通过认证，BCrypt 形同虚设。

**整改措施：** 删除明文比对分支，仅保留 `passwordEncoder.matches()`。

**改完应满足：** 数据库中非 BCrypt 格式的密码无法通过登录（errno=402）。

**验证结果：** 代码审查确认分支已删除 ✅

**遗留事项：** 已有明文密码用户需运维执行 BCrypt 迁移脚本（见 §4）。

---

### 2.2 问题：UUID Token 无完整性保护（T-S01）

**原代码：**
```java
session.setToken(UUID.randomUUID().toString().replace("-", ""));
sessionRepository.save(session);
```

**问题分析：** Token 为随机字符串，服务端仅做数据库查找，无法密码学验证来源和完整性。

**整改措施：**
- 新增 `JwtUtil`，使用 HS256 对 Claims 签名
- Claims 包含 `sub`(userId)、`username`、`jti`、`iat`、`exp`、`iss`
- `getUserByToken()` 改为验签 + 解析 + 查库

**改完应满足：** Token 为三段式 JWT；篡改任意字符后验签失败。

**验证结果：**
- 登录获取 Token，jwt.io 可解析 ✅
- 篡改末位字符，访问受保护接口返回 401 ✅

---

### 2.3 问题：访问控制可绕过（T-E01/T-E02）

**原代码：**
```java
// AuthFilter — 仅解析，不拦截
userOpt.ifPresent(user -> request.setAttribute("currentUser", user));
filterChain.doFilter(request, response); // 始终放行
```

**问题分析：** 若某 Controller 遗漏 `needLogin()` 检查，未认证用户可直接访问。

**整改措施：**
- 新增 `SecurityPathConfig` 集中管理公开路径白名单
- `AuthFilter` 对非公开路径：无有效用户 → HTTP 401 + JSON 响应，不继续 Filter Chain

**改完应满足：** 不带 Token 访问 `/wx/cart/index`、`/wx/order/list` 等均返回 401。

**验证结果：** 见 `reports/verification-report.md` ✅

---

### 2.4 问题：logout 无法失效 Token

**原代码：**
```java
public void logout(User user) {
    sessionRepository.deleteByUser(user);
}
```

**问题分析：** JWT 无状态，删除 DB 会话无法使已签发的 JWT 失效。

**整改措施：**
- 新增 `TokenRevocationService`，logout 时将 JWT 的 `jti` 加入内存黑名单
- `getUserByToken()` 验签后检查 jti 是否已被注销

**改完应满足：** logout 后使用原 Token 访问受保护接口返回 401。

**验证结果：** 见 `reports/verification-report.md` V-06 ✅

---

## 3. 新增/修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `util/JwtUtil.java` | 新增 | JWT 签发与验签 |
| `config/JwtProperties.java` | 新增 | JWT 配置项 |
| `config/SecurityPathConfig.java` | 新增 | 公开路径白名单 |
| `service/TokenRevocationService.java` | 新增 | logout 黑名单 |
| `service/AuthService.java` | 修改 | JWT 登录 + 移除明文密码 |
| `config/AuthFilter.java` | 修改 | 统一 401 拦截 |
| `controller/AuthController.java` | 修改 | logout 传递 Token |
| `config/AppConfig.java` | 修改 | 启用 JwtProperties |
| `pom.xml` | 新增 | jjwt 依赖 |
| `resources/application.properties.example` | 新增 | JWT 配置示例 |

---

## 4. 部署注意事项

### 4.1 JWT Secret 配置

```bash
# 生产环境通过环境变量注入，禁止提交真实密钥
export HMshop_JWT_SECRET="your-256-bit-random-secret-here"
```

### 4.2 HTTPS 配置

生产环境须在 Nginx/网关层配置 SSL 终止，确保登录密码不在明文 HTTP 信道传输。

### 4.3 历史明文密码迁移

对已存在的明文密码用户，需执行一次性迁移：

```sql
-- 示例：将已知明文密码 user1/password123 迁移为 BCrypt（需在应用中生成哈希后更新）
-- UPDATE shop_user SET password = '$2a$10$...' WHERE username = 'user1';
```

---

## 5. 验证总结

| 测试项 | 预期 | 实际 | 结论 |
|--------|------|------|------|
| 无 Token 访问购物车 | 401 | 401 | ✅ |
| 合法 Token 访问购物车 | 200 | 200 | ✅ |
| 篡改 Token | 401 | 401 | ✅ |
| logout 后重放 Token | 401 | 401 | ✅ |
| 登录返回 JWT 格式 | 三段式 | 三段式 | ✅ |
| 公开接口无 Token 访问 | 200 | 200 | ✅ |

**整改结论：** P0 安全风险已全部消除，P1 HTTPS 已文档化待部署配置。
