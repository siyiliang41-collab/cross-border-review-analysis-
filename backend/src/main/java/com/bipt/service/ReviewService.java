package com.bipt.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.bipt.entity.Review;

/**
 * 评论数据业务接口
 *
 * @author 梁思怡
 * @date 2026-07-09
 */
public interface ReviewService {

    /**
     * 分页查询 + 关键词搜索 + 品类/国家筛选
     */
    Page<Review> pageQuery(int page, int size, String keyword, String productId, String country);

    /**
     * 按评价ID查询单条
     */
    Review getById(Long evaluationId);

    /**
     * 新增评论
     */
    boolean save(Review review);

    /**
     * 更新评论
     */
    boolean update(Review review);

    /**
     * 删除评论
     */
    boolean delete(Long evaluationId);

    /**
     * 总记录数
     */
    long count();
}
