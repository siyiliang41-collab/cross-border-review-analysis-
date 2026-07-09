package com.bipt.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

/**
 * 评论实体类 — 映射 MySQL bipt_review 表（个体评论数据）
 * 每条记录对应一条速卖通用户评论，共23个字段
 *
 * @author 梁思怡
 * @date 2026-07-09
 */
@TableName("bipt_review")
public class Review {

    /** 评价ID（速卖通全局唯一） */
    @TableId(value = "evaluation_id", type = IdType.INPUT)
    private Long evaluationId;

    /** 商品ID（速卖通 productId） */
    @TableField("product_id")
    private String productId;

    /** 买家国家 ISO 代码 */
    @TableField("buyer_country")
    private String buyerCountry;

    /** 买家昵称 */
    @TableField("buyer_name")
    private String buyerName;

    /** 百分制评分（0-100） */
    @TableField("buyer_eval")
    private Integer buyerEval;

    /** 五分制评分（0.0-5.0） */
    @TableField("star_rating")
    private Double starRating;

    /** 原始评论文本（多语言） */
    @TableField("feedback")
    private String feedback;

    /** 英文翻译评论文本（平台自动翻译） */
    @TableField("feedback_translated")
    private String feedbackTranslated;

    /** 评价日期（格式: dd MMM yyyy 如 10 Nov 2025） */
    @TableField("eval_date")
    private String evalDate;

    /** SKU 信息（颜色/尺码/规格） */
    @TableField("sku_info")
    private String skuInfo;

    /** 物流方式 */
    @TableField("logistics")
    private String logistics;

    /** 点赞数 */
    @TableField("up_vote_count")
    private Integer upVoteCount;

    /** 点踩数 */
    @TableField("down_vote_count")
    private Integer downVoteCount;

    /** 是否带图（1=是 0=否） */
    @TableField("has_image")
    private Integer hasImage;

    /** 是否有追评（1=是 0=否） */
    @TableField("has_follow_up")
    private Integer hasFollowUp;

    /** 追评文本 */
    @TableField("add_feedback")
    private String addFeedback;

    /** 是否匿名（1=是 0=否） */
    @TableField("anonymous")
    private Integer anonymous;

    /** 平台AI标签1 */
    @TableField("label1")
    private String label1;

    /** 标签1的值 */
    @TableField("label_value1")
    private String labelValue1;

    /** 平台AI标签2 */
    @TableField("label2")
    private String label2;

    /** 标签2的值 */
    @TableField("label_value2")
    private String labelValue2;

    /** 平台AI标签3 */
    @TableField("label3")
    private String label3;

    /** 标签3的值 */
    @TableField("label_value3")
    private String labelValue3;

    // ========== Getter / Setter ==========

    public Long getEvaluationId() { return evaluationId; }
    public void setEvaluationId(Long evaluationId) { this.evaluationId = evaluationId; }

    public String getProductId() { return productId; }
    public void setProductId(String productId) { this.productId = productId; }

    public String getBuyerCountry() { return buyerCountry; }
    public void setBuyerCountry(String buyerCountry) { this.buyerCountry = buyerCountry; }

    public String getBuyerName() { return buyerName; }
    public void setBuyerName(String buyerName) { this.buyerName = buyerName; }

    public Integer getBuyerEval() { return buyerEval; }
    public void setBuyerEval(Integer buyerEval) { this.buyerEval = buyerEval; }

    public Double getStarRating() { return starRating; }
    public void setStarRating(Double starRating) { this.starRating = starRating; }

    public String getFeedback() { return feedback; }
    public void setFeedback(String feedback) { this.feedback = feedback; }

    public String getFeedbackTranslated() { return feedbackTranslated; }
    public void setFeedbackTranslated(String feedbackTranslated) { this.feedbackTranslated = feedbackTranslated; }

    public String getEvalDate() { return evalDate; }
    public void setEvalDate(String evalDate) { this.evalDate = evalDate; }

    public String getSkuInfo() { return skuInfo; }
    public void setSkuInfo(String skuInfo) { this.skuInfo = skuInfo; }

    public String getLogistics() { return logistics; }
    public void setLogistics(String logistics) { this.logistics = logistics; }

    public Integer getUpVoteCount() { return upVoteCount; }
    public void setUpVoteCount(Integer upVoteCount) { this.upVoteCount = upVoteCount; }

    public Integer getDownVoteCount() { return downVoteCount; }
    public void setDownVoteCount(Integer downVoteCount) { this.downVoteCount = downVoteCount; }

    public Integer getHasImage() { return hasImage; }
    public void setHasImage(Integer hasImage) { this.hasImage = hasImage; }

    public Integer getHasFollowUp() { return hasFollowUp; }
    public void setHasFollowUp(Integer hasFollowUp) { this.hasFollowUp = hasFollowUp; }

    public String getAddFeedback() { return addFeedback; }
    public void setAddFeedback(String addFeedback) { this.addFeedback = addFeedback; }

    public Integer getAnonymous() { return anonymous; }
    public void setAnonymous(Integer anonymous) { this.anonymous = anonymous; }

    public String getLabel1() { return label1; }
    public void setLabel1(String label1) { this.label1 = label1; }

    public String getLabelValue1() { return labelValue1; }
    public void setLabelValue1(String labelValue1) { this.labelValue1 = labelValue1; }

    public String getLabel2() { return label2; }
    public void setLabel2(String label2) { this.label2 = label2; }

    public String getLabelValue2() { return labelValue2; }
    public void setLabelValue2(String labelValue2) { this.labelValue2 = labelValue2; }

    public String getLabel3() { return label3; }
    public void setLabel3(String label3) { this.label3 = label3; }

    public String getLabelValue3() { return labelValue3; }
    public void setLabelValue3(String labelValue3) { this.labelValue3 = labelValue3; }
}
