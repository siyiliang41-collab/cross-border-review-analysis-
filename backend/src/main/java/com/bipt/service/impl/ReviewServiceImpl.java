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
 * 评论数据业务实现 — 使用 MyBatis Plus 分页插件标准分页
 * PaginationInnerInterceptor 已在 MyBatisPlusConfig 中注册（MySQL 方言）
 *
 * @author 梁思怡
 * @date 2026-07-09  更新：2026-07-14 切回标准 selectPage（分页插件已就绪）
 */
@Service
public class ReviewServiceImpl extends ServiceImpl<ReviewMapper, Review> implements ReviewService {

    @Override
    public Page<Review> pageQuery(int page, int size, String keyword, String productId, String country) {
        LambdaQueryWrapper<Review> wrapper = buildWrapper(keyword, productId, country);
        return baseMapper.selectPage(new Page<>(page, size), wrapper);
    }

    /**
     * 构建公共查询条件 — 关键词 + 品类 + 国家 + 降序
     */
    private LambdaQueryWrapper<Review> buildWrapper(String keyword, String productId, String country) {
        LambdaQueryWrapper<Review> wrapper = new LambdaQueryWrapper<>();

        if (StringUtils.hasText(keyword)) {
            wrapper.and(w -> w
                .like(Review::getFeedbackTranslated, keyword)
                .or()
                .like(Review::getFeedback, keyword)
            );
        }
        if (StringUtils.hasText(productId)) {
            wrapper.eq(Review::getProductId, productId);
        }
        if (StringUtils.hasText(country)) {
            wrapper.eq(Review::getBuyerCountry, country);
        }

        wrapper.orderByDesc(Review::getEvaluationId);
        return wrapper;
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
