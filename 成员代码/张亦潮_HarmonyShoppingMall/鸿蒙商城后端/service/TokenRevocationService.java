package com.hmshop.backend.service;

import org.springframework.stereotype.Service;

import java.util.Date;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 基于内存的 JWT 注销黑名单，logout 时将 jti 标记为失效直至原 Token 过期。
 * 生产环境可替换为 Redis 等分布式存储。
 */
@Service
public class TokenRevocationService {

    private final Map<String, Long> revokedTokens = new ConcurrentHashMap<>();

    public void revoke(String jti, Date expiration) {
        if (jti == null || expiration == null) {
            return;
        }
        revokedTokens.put(jti, expiration.getTime());
        purgeExpired();
    }

    public boolean isRevoked(String jti) {
        if (jti == null) {
            return false;
        }
        Long expiry = revokedTokens.get(jti);
        if (expiry == null) {
            return false;
        }
        if (expiry <= System.currentTimeMillis()) {
            revokedTokens.remove(jti);
            return false;
        }
        return true;
    }

    private void purgeExpired() {
        long now = System.currentTimeMillis();
        revokedTokens.entrySet().removeIf(entry -> entry.getValue() <= now);
    }
}
