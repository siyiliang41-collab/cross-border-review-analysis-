package com.bipt.config;

import com.baomidou.mybatisplus.annotation.DbType;
import com.baomidou.mybatisplus.extension.plugins.MybatisPlusInterceptor;
import com.baomidou.mybatisplus.extension.plugins.inner.PaginationInnerInterceptor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * MyBatis Plus 配置 — 注册分页插件
 *
 * @author 梁思怡
 * @date 2026-07-09
 */
@Configuration
public class MyBatisPlusConfig {

    /**
     * MyBatis Plus 拦截器：注册分页插件（MySQL 方言）
     */
    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        PaginationInnerInterceptor paginationInner = new PaginationInnerInterceptor(DbType.MYSQL);
        // 溢出处理：页码超过最大页时回到第一页
        paginationInner.setOverflow(true);
        interceptor.addInnerInterceptor(paginationInner);
        return interceptor;
    }
}
