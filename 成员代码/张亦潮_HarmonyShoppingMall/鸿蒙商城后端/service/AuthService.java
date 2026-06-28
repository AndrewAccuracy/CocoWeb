package com.hmshop.backend.service;

import com.hmshop.backend.common.ApiResponse;
import com.hmshop.backend.dto.LoginResponse;
import com.hmshop.backend.dto.UserInfoDto;
import com.hmshop.backend.entity.User;
import com.hmshop.backend.repository.UserRepository;
import com.hmshop.backend.util.JwtUtil;
import io.jsonwebtoken.Claims;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.Optional;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;
    private final TokenRevocationService tokenRevocationService;

    public Optional<User> getUserByToken(String token) {
        if (!StringUtils.hasText(token)) {
            return Optional.empty();
        }
        Optional<Claims> claimsOpt = jwtUtil.parseToken(token);
        if (claimsOpt.isEmpty()) {
            return Optional.empty();
        }
        Claims claims = claimsOpt.get();
        if (tokenRevocationService.isRevoked(claims.getId())) {
            return Optional.empty();
        }
        try {
            Long userId = Long.parseLong(claims.getSubject());
            return userRepository.findById(userId);
        } catch (NumberFormatException ex) {
            return Optional.empty();
        }
    }

    public ApiResponse<LoginResponse> login(String username, String rawPassword) {
        Optional<User> userOpt = userRepository.findByUsername(username);
        if (userOpt.isEmpty()) {
            return ApiResponse.fail(402, "账号或密码错误");
        }
        User user = userOpt.get();
        if (!passwordEncoder.matches(rawPassword, user.getPassword())) {
            return ApiResponse.fail(402, "账号或密码错误");
        }

        String token = jwtUtil.generateToken(user.getId(), user.getUsername());
        LoginResponse resp = new LoginResponse(new UserInfoDto(user.getNickname(), user.getAvatar()), token);
        return ApiResponse.ok(resp);
    }

    public void logout(String token) {
        jwtUtil.parseToken(token).ifPresent(claims -> tokenRevocationService.revoke(claims.getId(), claims.getExpiration()));
    }
}
