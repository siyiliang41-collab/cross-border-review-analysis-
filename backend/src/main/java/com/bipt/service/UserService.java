package com.bipt.service;

import com.bipt.entity.User;
import java.util.Map;

/**
 * 用户认证业务接口
 * @author 梁思怡
 */
public interface UserService {

    /** 注册，返回 token + role */
    Map<String, Object> register(String username, String password);

    /** 登录，返回 token + role，失败抛异常 */
    Map<String, Object> login(String username, String password);
}
