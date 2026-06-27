package com.hmshop.backend.controller;

import com.hmshop.backend.common.ApiResponse;
import com.hmshop.backend.dto.LoginRequest;
import com.hmshop.backend.dto.LoginResponse;
import com.hmshop.backend.dto.UserProfileDto;
import com.hmshop.backend.entity.User;
import com.hmshop.backend.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/wx/auth")
@RequiredArgsConstructor
public class AuthController extends BaseController {

    private final AuthService authService;

    @PostMapping("/login")
    public ApiResponse<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        return authService.login(request.getUsername(), request.getPassword());
    }

    @GetMapping("/info")
    public ApiResponse<UserProfileDto> info(HttpServletRequest request) {
        User user = getCurrentUser(request);
        if (user == null) {
            return needLogin();
        }
        UserProfileDto profile = new UserProfileDto(user.getGender(), user.getNickname(), user.getMobile(),
                user.getAvatar());
        return ApiResponse.ok(profile);
    }

    @PostMapping("/logout")
    public ApiResponse<Void> logout(HttpServletRequest request) {
        String token = extractToken(request);
        if (StringUtils.hasText(token)) {
            authService.logout(token);
        }
        return ApiResponse.ok(null);
    }

    private String extractToken(HttpServletRequest request) {
        String authorization = request.getHeader(HttpHeaders.AUTHORIZATION);
        if (StringUtils.hasText(authorization) && authorization.startsWith("Bearer ")) {
            return authorization.substring(7).trim();
        }
        return request.getHeader("x-litemall-token");
    }
}
