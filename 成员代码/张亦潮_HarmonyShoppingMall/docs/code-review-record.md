# 生成结果检查记录

**模块：** 鸿蒙商城认证模块  
**检查人员：** 张亦潮  
**检查日期：** 2026-06-27

---

## 1. 检查流程

```
AI 生成代码
    │
    ▼
第一层：对照 Prompt 约束逐项检查（security-checklist.md §A）
    │
    ▼
第二层：人工业务逻辑审查（security-checklist.md §B）
    │
    ▼
第三层：验收标准执行测试（security-checklist.md §V）
    │
    ▼
发现问题 → 追加 Prompt 纠正 → 重新检查
    │
    ▼
通过 → 提交 PR
```

---

## 2. 第一层检查详情（对照 Prompt）

### 2.1 AuthService.java

| 检查点 | Prompt 要求 | 实际代码 | 结论 |
|--------|-------------|----------|------|
| 密码校验 | 仅 BCrypt | L52: `passwordEncoder.matches()` | ✅ |
| 无明文回退 | 删除 equals 分支 | 原 L43-44 已删除 | ✅ |
| Token 生成 | JWT 非 UUID | L56: `jwtUtil.generateToken()` | ✅ |
| 会话表写入 | 不再写 user_session | 无 sessionRepository 调用 | ✅ |

### 2.2 JwtUtil.java

| 检查点 | Prompt 要求 | 实际代码 | 结论 |
|--------|-------------|----------|------|
| 签名算法 | HS256 | `signWith(signingKey())` HMAC | ✅ |
| Claims 完整性 | sub/username/jti/exp/iss | builder 中包含全部字段 | ✅ |
| 验签失败处理 | 返回 empty 而非抛异常 | catch JwtException → Optional.empty() | ✅ |

### 2.3 AuthFilter.java

| 检查点 | Prompt 要求 | 实际代码 | 结论 |
|--------|-------------|----------|------|
| 统一拦截 | 非公开路径 401 | L40-43: isPublicPath + writeUnauthorized | ✅ |
| Bearer 优先 | Authorization 头 | extractToken() 先检查 Bearer | ✅ |
| 响应格式 | ApiResponse JSON | objectMapper.writeValue + fail(501) | ✅ |

---

## 3. 发现的偏差与处置

### 偏差 #1：logout 未实现服务端 Token 失效

- **发现阶段：** 第一层检查 A-07
- **问题描述：** Prompt #2 初版 `AuthService.logout(User user)` 仅删除 DB 会话，JWT 方案下无失效机制
- **处置方式：** 追加 Prompt #3，新增 `TokenRevocationService`，改为 `logout(String token)` 按 jti 黑名单
- **验证：** V-06 logout 后重放 Token 返回 401 ✅

### 偏差 #2：AuthFilter 未拦截未认证请求

- **发现阶段：** 第一层检查 A-06
- **问题描述：** 原 Filter 设计为"有 Token 就解析"，Prompt #2 未改造拦截逻辑
- **处置方式：** 追加 Prompt #3，新增 `SecurityPathConfig` + Filter 401 拦截
- **验证：** V-03 无 Token 访问 cart 返回 401 ✅

---

## 4. 人工审查补充意见

1. **双保险策略合理：** Controller 层 `needLogin()` 与 Filter 层 401 并存，降低单点遗漏风险
2. **x-litemall-token 兼容：** 仅为前端迁移过渡，不应作为长期方案
3. **数据库密码迁移：** 需在部署说明中提醒运维对明文密码用户做 BCrypt 重哈希

---

## 5. 检查结论

经三层检查，AI 生成代码在偏差纠正后满足 `constraint-doc.md` 全部 Hard Constraints 和 Mandatory Requirements。可进入 PR 提交阶段。
