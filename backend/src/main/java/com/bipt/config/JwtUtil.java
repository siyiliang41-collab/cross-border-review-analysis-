package com.bipt.config;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

/**
 * JWT 工具类 — 生成/解析/校验 Token
 * @author 梁思怡
 */
public class JwtUtil {

    private static final String SECRET = "bipt-cross-border-review-system-2026-07-09-secret-key!!";
    private static final SecretKey KEY = Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8));
    private static final long EXPIRE_MS = 24 * 60 * 60 * 1000; // 24小时

    /** 生成 JWT */
    public static String generate(Long userId, String username, String role) {
        return Jwts.builder()
                .subject(username)
                .claim("userId", userId)
                .claim("role", role)
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + EXPIRE_MS))
                .signWith(KEY)
                .compact();
    }

    /** 解析 JWT，无效则返回 null */
    public static Claims parse(String token) {
        try {
            return Jwts.parser()
                    .verifyWith(KEY)
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
        } catch (Exception e) {
            return null;
        }
    }

    /** 是否管理员 */
    public static boolean isAdmin(Claims claims) {
        return claims != null && "admin".equals(claims.get("role"));
    }
}
