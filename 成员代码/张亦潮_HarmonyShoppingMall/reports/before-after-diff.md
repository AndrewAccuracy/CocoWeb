# 整改前后行为对比

**模块：** 鸿蒙商城认证模块  
**对比日期：** 2026-06-27

---

## 1. 认证 Token 机制

| 维度 | 整改前 | 整改后 |
|------|--------|--------|
| Token 类型 | UUID 随机字符串（32 位 hex） | JWT（Header.Payload.Signature） |
| 签名算法 | 无 | HS256 HMAC |
| 存储方式 | 写入 `user_session` 数据库表 | 无状态，客户端持有 |
| 完整性验证 | 数据库 lookup，无法验签 | `JwtUtil.parseToken()` 密码学验签 |
| 传递方式 | 仅 `x-litemall-token` Header | 优先 `Authorization: Bearer`，兼容旧 Header |
| 过期机制 | DB 字段 `expire_at`（3 天） | JWT `exp` Claim（默认 24h，可配置） |
| 注销机制 | 删除 DB 会话记录 | jti 加入 `TokenRevocationService` 黑名单 |

**示例对比：**

```
# 整改前 Token
a1b2c3d4e5f6789012345678abcdef01

# 整改后 Token（解码 Payload 示意）
{
  "sub": "1",
  "username": "demo",
  "jti": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "iss": "hmshop-backend",
  "iat": 1719460800,
  "exp": 1719547200
}
```

---

## 2. 密码校验逻辑

| 维度 | 整改前 | 整改后 |
|------|--------|--------|
| 校验方式 | BCrypt **或** 明文 equals | **仅** BCrypt matches |
| 明文密码兼容 | ✅ 允许 | ❌ 禁止 |
| 代码位置 | `AuthService.login()` L43-44 | `AuthService.login()` L52 |

**安全影响：**

- 整改前：数据库中明文密码 `"123456"` 可直接登录
- 整改后：仅 `$2a$10$...` 格式 BCrypt 哈希可通过校验

---

## 3. 访问控制行为

| 测试场景 | 整改前 | 整改后 |
|----------|--------|--------|
| 无 Token 访问 `GET /wx/goods/list` | 200（公开） | 200（公开） |
| 无 Token 访问 `GET /wx/cart/index` | 200 + errno=501（Controller 层拒绝） | **HTTP 401** + errno=501（Filter 层拦截） |
| 无 Token 访问 `GET /wx/order/list` | 200 + errno=501 | **HTTP 401** + errno=501 |
| 伪造 Token 访问受保护接口 | 200 + errno=501（UUID 不存在） | **HTTP 401**（验签失败） |
| Controller 遗漏 needLogin() | **可能绕过**（Filter 不拦截） | **Filter 兜底拦截** |

**关键差异：** 整改前鉴权完全依赖各 Controller 自觉检查；整改后 Filter 对非白名单路径强制拦截，即使 Controller 遗漏也无法绕过。

---

## 4. 登录接口响应

| 维度 | 整改前 | 整改后 |
|------|--------|--------|
| 请求体 | `{"username":"demo","password":"123456"}` | 相同 |
| 成功响应 | `{"errno":0,"data":{"token":"uuid...","userInfo":{...}}}` | `{"errno":0,"data":{"token":"eyJhbG...","userInfo":{...}}}` |
| 密码传输 | HTTP 明文 JSON | HTTP 明文 JSON（**部署层需 HTTPS**） |

---

## 5. 注销接口行为

| 维度 | 整改前 | 整改后 |
|------|--------|--------|
| 服务端失效 | 删除 DB 会话 | jti 加入黑名单 |
| 注销后 Token 可用性 | 取决于 DB 记录是否删除 | 黑名单拦截，Token 立即失效 |
| 验证 | 注销后同 Token 访问 → errno=501 | 注销后同 Token 访问 → HTTP 401 |

---

## 6. 总结

| 安全属性 | 整改前 | 整改后 |
|----------|--------|--------|
| 机密性（密码存储） | ⚠️ 弱（明文兼容） | ✅ BCrypt 强制 |
| 完整性（Token） | ❌ 无 | ✅ HS256 签名 |
| 可用性（认证服务） | ✅ 正常 | ✅ 正常 |
| 访问控制 | ⚠️ 分散、可遗漏 | ✅ 统一 Filter 拦截 |
| 传输安全 | ❌ 无 HTTPS 强制 | ⏳ 部署层要求 |

**结论：** 整改后在认证完整性、密码存储、访问控制三个维度有实质性安全提升；传输层 HTTPS 需部署配置完成最后一环。
