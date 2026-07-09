-- ============================================================
-- DDL：bipt_review 评论个体数据表
-- 用于数据管理模块 CRUD 操作
-- 创建日期：2026-07-09  作者：梁思怡
-- ============================================================

CREATE TABLE IF NOT EXISTS `bipt_review` (
    `evaluation_id`       BIGINT        NOT NULL PRIMARY KEY    COMMENT '评价ID（速卖通全局唯一）',
    `product_id`          VARCHAR(64)   DEFAULT NULL            COMMENT '商品ID',
    `buyer_country`       VARCHAR(8)    DEFAULT NULL            COMMENT '买家国家 ISO 代码',
    `buyer_name`          VARCHAR(128)  DEFAULT NULL            COMMENT '买家昵称',
    `buyer_eval`          INT           DEFAULT NULL            COMMENT '百分制评分 0-100',
    `star_rating`         DOUBLE        DEFAULT NULL            COMMENT '五分制评分 0.0-5.0',
    `feedback`            TEXT                                  COMMENT '原始评论文本（多语言）',
    `feedback_translated` TEXT                                  COMMENT '英文翻译评论',
    `eval_date`           VARCHAR(32)   DEFAULT NULL            COMMENT '评价日期 dd MMM yyyy',
    `sku_info`            VARCHAR(256)  DEFAULT NULL            COMMENT 'SKU信息（颜色/尺码/规格）',
    `logistics`           VARCHAR(256)  DEFAULT NULL            COMMENT '物流方式',
    `up_vote_count`       INT           DEFAULT 0               COMMENT '点赞数',
    `down_vote_count`     INT           DEFAULT 0               COMMENT '点踩数',
    `has_image`           INT           DEFAULT 0               COMMENT '是否带图 1=是 0=否',
    `has_follow_up`       INT           DEFAULT 0               COMMENT '是否有追评 1=是 0=否',
    `add_feedback`        TEXT                                  COMMENT '追评文本',
    `anonymous`           INT           DEFAULT 0               COMMENT '是否匿名 1=是 0=否',
    `label1`              VARCHAR(128)  DEFAULT NULL            COMMENT '平台AI标签1',
    `label_value1`        VARCHAR(256)  DEFAULT NULL            COMMENT '标签1的值',
    `label2`              VARCHAR(128)  DEFAULT NULL            COMMENT '平台AI标签2',
    `label_value2`        VARCHAR(256)  DEFAULT NULL            COMMENT '标签2的值',
    `label3`              VARCHAR(128)  DEFAULT NULL            COMMENT '平台AI标签3',
    `label_value3`        VARCHAR(256)  DEFAULT NULL            COMMENT '标签3的值',
    INDEX `idx_product`   (`product_id`),
    INDEX `idx_country`   (`buyer_country`),
    INDEX `idx_star`      (`star_rating`),
    INDEX `idx_date`      (`eval_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='速卖通商品评论数据表 — 用于CRUD管理模块';
