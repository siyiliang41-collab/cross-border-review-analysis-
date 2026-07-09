package com.bipt.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.bipt.entity.Review;
import org.apache.ibatis.annotations.Mapper;

/**
 * 评论数据映射接口 — 继承 MyBatis Plus BaseMapper
 * 自动获得 selectPage / insert / updateById / deleteById 等内置方法
 *
 * @author 梁思怡
 * @date 2026-07-09
 */
@Mapper
public interface ReviewMapper extends BaseMapper<Review> {
    // BaseMapper 已提供全部 CRUD + 分页方法，无需手写 SQL
}
