package com.bipt.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.bipt.config.JwtUtil;
import com.bipt.entity.User;
import com.bipt.mapper.UserMapper;
import com.bipt.service.UserService;
import at.favre.lib.crypto.bcrypt.BCrypt;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

/**
 * 用户认证业务实现
 * @author 梁思怡
 */
@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {

    @Override
    public Map<String, Object> register(String username, String password) {
        // 检查用户名是否已存在
        LambdaQueryWrapper<User> w = new LambdaQueryWrapper<>();
        w.eq(User::getUsername, username);
        if (baseMapper.selectCount(w) > 0) {
            throw new RuntimeException("用户名已存在");
        }

        // BCrypt 加密密码
        String hash = BCrypt.withDefaults().hashToString(12, password.toCharArray());

        // 插入用户（默认 role = user）
        User user = new User();
        user.setUsername(username);
        user.setPassword(hash);
        user.setRole("user");
        baseMapper.insert(user);

        // 生成 JWT
        String token = JwtUtil.generate(user.getId(), username, "user");

        Map<String, Object> result = new HashMap<>();
        result.put("token", token);
        result.put("role", "user");
        result.put("username", username);
        return result;
    }

    @Override
    public Map<String, Object> login(String username, String password) {
        LambdaQueryWrapper<User> w = new LambdaQueryWrapper<>();
        w.eq(User::getUsername, username);
        User user = baseMapper.selectOne(w);

        if (user == null) {
            throw new RuntimeException("用户名或密码错误");
        }

        // 验证密码
        BCrypt.Result verify = BCrypt.verifyer().verify(password.toCharArray(), user.getPassword());
        if (!verify.verified) {
            throw new RuntimeException("用户名或密码错误");
        }

        // 生成 JWT
        String token = JwtUtil.generate(user.getId(), username, user.getRole());

        Map<String, Object> result = new HashMap<>();
        result.put("token", token);
        result.put("role", user.getRole());
        result.put("username", username);
        return result;
    }
}
