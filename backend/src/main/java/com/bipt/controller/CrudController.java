package com.bipt.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.bipt.entity.Review;
import com.bipt.service.ReviewService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * CRUD 控制器 — 评论数据增删改查 + 分页 + 搜索
 * 满足课程 MVC 分层要求：Controller → Service → Mapper → Entity
 *
 * @author 梁思怡
 * @date 2026-07-09
 */
@RestController
@RequestMapping("/api/crud")
public class CrudController {

    @Autowired
    private ReviewService reviewService;

    /**
     * 分页查询 + 关键词搜索 + 品类/国家筛选
     * GET /api/crud/reviews?page=1&size=20&keyword=good&productId=3256808363596774&country=US
     */
    @GetMapping("/reviews")
    public Map<String, Object> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String productId,
            @RequestParam(required = false) String country) {

        Page<Review> result = reviewService.pageQuery(page, size, keyword, productId, country);

        Map<String, Object> resp = new HashMap<>();
        resp.put("code", 200);
        resp.put("data", result.getRecords());          // 当前页数据
        resp.put("total", result.getTotal());            // 总记录数
        resp.put("page", result.getCurrent());           // 当前页
        resp.put("size", result.getSize());              // 每页大小
        resp.put("pages", result.getPages());            // 总页数
        return resp;
    }

    /**
     * 查单条
     * GET /api/crud/reviews/30096273310796453
     */
    @GetMapping("/reviews/{id}")
    public Map<String, Object> getById(@PathVariable String id) {
        Review review = reviewService.getById(Long.parseLong(id));
        Map<String, Object> resp = new HashMap<>();
        resp.put("code", review != null ? 200 : 404);
        resp.put("data", review);
        resp.put("message", review != null ? "OK" : "记录不存在");
        return resp;
    }

    /**
     * 新增评论
     * POST /api/crud/reviews
     */
    @PostMapping("/reviews")
    public Map<String, Object> create(@RequestBody Review review) {
        boolean ok = reviewService.save(review);
        Map<String, Object> resp = new HashMap<>();
        resp.put("code", ok ? 200 : 500);
        resp.put("message", ok ? "新增成功" : "新增失败");
        return resp;
    }

    /**
     * 更新评论
     * PUT /api/crud/reviews/30096273310796453
     */
    @PutMapping("/reviews/{id}")
    public Map<String, Object> update(@PathVariable String id, @RequestBody Review review) {
        review.setEvaluationId(Long.parseLong(id));
        boolean ok = reviewService.update(review);
        Map<String, Object> resp = new HashMap<>();
        resp.put("code", ok ? 200 : 500);
        resp.put("message", ok ? "更新成功" : "更新失败");
        return resp;
    }

    /**
     * 删除评论
     * DELETE /api/crud/reviews/30096273310796453
     */
    @DeleteMapping("/reviews/{id}")
    public Map<String, Object> delete(@PathVariable String id) {
        boolean ok = reviewService.delete(Long.parseLong(id));
        Map<String, Object> resp = new HashMap<>();
        resp.put("code", ok ? 200 : 500);
        resp.put("message", ok ? "删除成功" : "删除失败（可能记录不存在）");
        return resp;
    }

    /**
     * 统计数据（用于数据管理页面顶部概览）
     * GET /api/crud/stats
     */
    @GetMapping("/stats")
    public Map<String, Object> stats() {
        long total = reviewService.count();
        Map<String, Object> resp = new HashMap<>();
        resp.put("code", 200);
        resp.put("totalReviews", total);
        resp.put("message", "共 " + total + " 条评论数据");
        return resp;
    }
}
