package com.bipt.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.bipt.entity.Review;
import com.bipt.mapper.ReviewMapper;
import com.bipt.service.ReviewService;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

/**
 * 评论数据业务实现 — 分页查询 + 关键词搜索 + 品类/国家筛选
 * 继承 ServiceImpl 获得 MyBatis Plus 内置的 save/update/remove/page 等方法
 *
 * @author 梁思怡
 * @date 2026-07-09
 */
@Service
public class ReviewServiceImpl extends ServiceImpl<ReviewMapper, Review> implements ReviewService {

    @Override
    public Page<Review> pageQuery(int page, int size, String keyword, String productId, String country) {
        // 构建查询条件
        LambdaQueryWrapper<Review> wrapper = new LambdaQueryWrapper<>();

        // 关键词搜索：英文翻译文本 + 原始文本 模糊匹配
        if (StringUtils.hasText(keyword)) {
            wrapper.and(w -> w
                .like(Review::getFeedbackTranslated, keyword)
                .or()
                .like(Review::getFeedback, keyword)
            );
        }

        // 品类筛选
        if (StringUtils.hasText(productId)) {
            wrapper.eq(Review::getProductId, productId);
        }

        // 国家筛选
        if (StringUtils.hasText(country)) {
            wrapper.eq(Review::getBuyerCountry, country);
        }

        // 按评价ID降序排列
        wrapper.orderByDesc(Review::getEvaluationId);

        // 分页查询
        Page<Review> pageObj = new Page<>(page, size);
        return baseMapper.selectPage(pageObj, wrapper);
    }

    @Override
    public Review getById(Long evaluationId) {
        return baseMapper.selectById(evaluationId);
    }

    @Override
    public boolean save(Review review) {
        return baseMapper.insert(review) > 0;
    }

    @Override
    public boolean update(Review review) {
        return baseMapper.updateById(review) > 0;
    }

    @Override
    public boolean delete(Long evaluationId) {
        return baseMapper.deleteById(evaluationId) > 0;
    }

    @Override
    public long count() {
        return baseMapper.selectCount(null);
    }
}
