# API 接口清单

> 跨境电商评论情感挖掘与选品决策支持系统 — 昌平champion盛世  
> 后端：SpringBoot 3.2 | 地址：`http://192.168.229.101:8080/api`

---

## 一、概览

| 方法 | 端点 | 说明 | 数据源表 |
|---|---|---|---|
| GET | `/api/overview` | 整体概览（品类数+均分） | ads_product_rating |
| GET | `/api/quality/report` | 数据质量分析报告 | 多表聚合 |

## 二、商品 & 评分

| 方法 | 端点 | 说明 | 数据源表 |
|---|---|---|---|
| GET | `/api/products/rating` | 全品类评分排名 | ads_product_rating |
| GET | `/api/scorecard` | 选品评分卡（推荐指数排序） | ads_product_scorecard |
| GET | `/api/sentiment/product` | 各品类情感正/中/负面率 | ads_sentiment_product |

## 三、国家 & 地理分析

| 方法 | 端点 | 说明 | 数据源表 |
|---|---|---|---|
| GET | `/api/countries/top15` | TOP15 国家评分排名 | ads_country_top15 |
| GET | `/api/countries/list` | 国家列表（下拉框） | ads_country_top15 |
| GET | `/api/matrix` | 国家×商品适配度矩阵 | ads_country_product_matrix |

## 四、时间趋势

| 方法 | 端点 | 说明 | 数据源表 |
|---|---|---|---|
| GET | `/api/trend/monthly` | 全局月度评论量&评分趋势 | ads_monthly_trend |
| GET | `/api/trend/{productId}/country/{code}` | 指定国家×商品的月度趋势 | ads_country_monthly_trend |

## 五、SKU & 物流

| 方法 | 端点 | 说明 | 数据源表 |
|---|---|---|---|
| GET | `/api/sku/analysis` | 各品类 SKU 分析 | ads_sku_analysis |
| GET | `/api/sku/{productId}/country/{code}` | 指定国家×商品的 SKU 偏好 | ads_sku_country_pref |
| GET | `/api/logistics` | 物流方式满意度对比 | ads_logistics |
| GET | `/api/image/followup` | 带图/追评行为统计 | ads_image_followup |

## 六、特征 & ABSA

| 方法 | 端点 | 说明 | 数据源表 |
|---|---|---|---|
| GET | `/api/feature/{productId}` | 指定商品的产品特征分析 | ads_feature_country_product |
| GET | `/api/feature/{productId}/country/{code}` | 指定国家×商品的特征分析 | ads_feature_country_product |

## 七、选品决策面板

| 方法 | 端点 | 说明 |
|---|---|---|
| GET | `/api/decision/{productId}` | 综合决策建议（排名+最佳市场+优势/痛点+推荐SKU+物流+好评率） |

一次返回7组数据：评分排名、TOP3 最佳市场、TOP3 优势特征、TOP3 痛点特征、推荐 SKU、推荐物流、好评率。

## 八、返回格式

全部接口返回 JSON，示例：

```json
{
  "product_id": "3256808363596774",
  "total_reviews": 4917,
  "avg_star": 4.08
}
```

质量报告接口返回结构见下方示例：

```json
{
  "overview": {"product_count":5, "country_count":15, "total_reviews":19248},
  "timeSpan": {"earliest":"2025-07", "latest":"2026-07", "months":13},
  "cleaning": {"rawRows":19271, "cleanedRows":19248, "removedRows":23, "removalRate":"0.1%"},
  "productDetail": [...],
  "monthlyDetail": [...],
  "topCountries": [...]
}
```
