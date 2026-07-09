package com.bipt.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.bipt.entity.Review;
import com.bipt.mapper.ReviewMapper;
import com.bipt.service.ReviewService;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.List;

/**
 * 评论数据业务实现 — 手动分页（不依赖 MyBatis Plus 分页插件）
 * 因 VM Maven 未正确下载 PaginationInnerInterceptor，改用 COUNT + LIMIT 手动分页
 *
 * @author 梁思怡
 * @date 2026-07-09
 */
@Service
public class ReviewServiceImpl extends ServiceImpl<ReviewMapper, Review> implements ReviewService {

    @Override
    public Page<Review> pageQuery(int page, int size, String keyword, String productId, String country) {
        // ① 先查总数（不带 LIMIT）
        LambdaQueryWrapper<Review> countWrapper = buildWrapper(keyword, productId, country);
        long total = baseMapper.selectCount(countWrapper);

        // ② 再查当前页数据（带 LIMIT）
        LambdaQueryWrapper<Review> dataWrapper = buildWrapper(keyword, productId, country);
        int offset = (page - 1) * size;
        dataWrapper.last("LIMIT " + offset + ", " + size);
        List<Review> records = baseMapper.selectList(dataWrapper);

        // ③ 组装分页结果
        Page<Review> pageObj = new Page<>(page, size, total);
        pageObj.setRecords(records);
        return pageObj;
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
