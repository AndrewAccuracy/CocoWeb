package com.hmshop.backend.config;

import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;

import java.util.List;

/**
 * 定义公开接口与需认证接口的路径规则，供 AuthFilter 统一鉴权使用。
 */
@Component
public class SecurityPathConfig {

    private static final AntPathMatcher PATH_MATCHER = new AntPathMatcher();

    private static final List<String> PUBLIC_PATHS = List.of(
            "/wx/auth/login",
            "/wx/home/**",
            "/wx/goods/**",
            "/wx/catalog/**",
            "/wx/brand/**",
            "/wx/groupon/**",
            "/wx/topic/**",
            "/wx/ai/recommend",
            "/wx/ai/chat"
    );

    public boolean isPublicPath(String uri, String method) {
        if (HttpMethod.OPTIONS.matches(method)) {
            return true;
        }
        return PUBLIC_PATHS.stream().anyMatch(pattern -> PATH_MATCHER.match(pattern, uri));
    }
}
