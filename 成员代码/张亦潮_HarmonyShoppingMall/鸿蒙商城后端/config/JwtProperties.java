package com.hmshop.backend.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "hmshop.jwt")
public class JwtProperties {

    /**
     * HS256 签名密钥，生产环境必须通过环境变量注入，禁止硬编码或提交到版本库。
     */
    private String secret = "change-me-in-production-use-env-var";

    /**
     * Access Token 有效期（秒），默认 24 小时。
     */
    private long expirationSeconds = 86400;

    /**
     * JWT 签发者标识。
     */
    private String issuer = "hmshop-backend";
}
