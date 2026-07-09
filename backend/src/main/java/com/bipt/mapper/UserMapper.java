package com.bipt.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.bipt.entity.User;
import org.apache.ibatis.annotations.Mapper;

/**
 * 用户数据映射接口
 * @author 梁思怡
 */
@Mapper
public interface UserMapper extends BaseMapper<User> {
}
