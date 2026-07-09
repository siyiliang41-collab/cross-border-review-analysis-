package com.bipt.config;

import io.jsonwebtoken.Claims;
import jakarta.servlet.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * 权限拦截器 — POST/PUT/DELETE /api/crud/** 需要 admin 角色
 * @author 梁思怡
 */
@Component
public class AuthInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // 只拦截增删改操作（GET 请求放行）
        String method = request.getMethod();
        String path = request.getRequestURI();

        // 只保护 CRUD 的增删改
        if (!path.startsWith("/api/crud/") || "GET".equalsIgnoreCase(method)) {
            return true;
        }

        // 从 Header 取 token
        String token = request.getHeader("Authorization");
        if (token == null || token.isEmpty()) {
            response.setStatus(403);
            response.getWriter().write("{\"code\":403,\"message\":\"请先登录\"}");
            return false;
        }

        if (token.startsWith("Bearer ")) {
            token = token.substring(7);
        }

        Claims claims = JwtUtil.parse(token);
        if (claims == null) {
            response.setStatus(403);
            response.getWriter().write("{\"code\":403,\"message\":\"登录已过期，请重新登录\"}");
            return false;
        }

        if (!JwtUtil.isAdmin(claims)) {
            response.setStatus(403);
            response.getWriter().write("{\"code\":403,\"message\":\"无权限，仅管理员可操作\"}");
            return false;
        }

        // 将用户信息放入 request
        request.setAttribute("username", claims.getSubject());
        request.setAttribute("role", claims.get("role"));
        return true;
    }
}
