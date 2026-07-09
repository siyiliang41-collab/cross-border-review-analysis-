package com.bipt.controller;

import com.bipt.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * 用户认证控制器 — 注册/登录
 * @author 梁思怡
 */
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private UserService userService;

    /** 注册 */
    @PostMapping("/register")
    public Map<String, Object> register(@RequestBody Map<String, String> body) {
        String username = body.get("username");
        String password = body.get("password");

        if (username == null || username.trim().isEmpty() || password == null || password.trim().isEmpty()) {
            Map<String, Object> err = new HashMap<>();
            err.put("code", 400);
            err.put("message", "用户名和密码不能为空");
            return err;
        }

        try {
            Map<String, Object> result = userService.register(username.trim(), password);
            result.put("code", 200);
            result.put("message", "注册成功");
            return result;
        } catch (RuntimeException e) {
            Map<String, Object> err = new HashMap<>();
            err.put("code", 400);
            err.put("message", e.getMessage());
            return err;
        }
    }

    /** 登录 */
    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody Map<String, String> body) {
        String username = body.get("username");
        String password = body.get("password");

        if (username == null || username.trim().isEmpty() || password == null || password.trim().isEmpty()) {
            Map<String, Object> err = new HashMap<>();
            err.put("code", 400);
            err.put("message", "用户名和密码不能为空");
            return err;
        }

        try {
            Map<String, Object> result = userService.login(username.trim(), password);
            result.put("code", 200);
            result.put("message", "登录成功");
            return result;
        } catch (RuntimeException e) {
            Map<String, Object> err = new HashMap<>();
            err.put("code", 401);
            err.put("message", e.getMessage());
            return err;
        }
    }
}
