package com.hmshop.backend.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hmshop.backend.common.ApiResponse;
import com.hmshop.backend.entity.User;
import com.hmshop.backend.service.AuthService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Optional;

@Component
@RequiredArgsConstructor
public class AuthFilter extends OncePerRequestFilter {

    private static final String LEGACY_TOKEN_HEADER = "x-litemall-token";

    private final AuthService authService;
    private final SecurityPathConfig securityPathConfig;
    private final ObjectMapper objectMapper;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        String token = extractToken(request);
        Optional<User> userOpt = authService.getUserByToken(token);
        userOpt.ifPresent(user -> request.setAttribute("currentUser", user));

        if (!securityPathConfig.isPublicPath(request.getRequestURI(), request.getMethod()) && userOpt.isEmpty()) {
            writeUnauthorized(response);
            return;
        }

        filterChain.doFilter(request, response);
    }

    private String extractToken(HttpServletRequest request) {
        String authorization = request.getHeader(HttpHeaders.AUTHORIZATION);
        if (StringUtils.hasText(authorization) && authorization.startsWith("Bearer ")) {
            return authorization.substring(7).trim();
        }
        String legacyToken = request.getHeader(LEGACY_TOKEN_HEADER);
        if (!StringUtils.hasText(legacyToken)) {
            legacyToken = request.getHeader("X-Litemall-Token");
        }
        return legacyToken;
    }

    private void writeUnauthorized(HttpServletResponse response) throws IOException {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        objectMapper.writeValue(response.getWriter(), ApiResponse.fail(501, "请登录"));
    }
}
