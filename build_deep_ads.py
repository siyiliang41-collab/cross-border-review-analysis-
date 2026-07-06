# -*- coding: utf-8 -*-
"""深度分析 ADS 表构建 — 5张新表 + 导出MySQL"""
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder \
    .appName("DeepADSAnalysis") \
    .config("spark.sql.adaptive.enabled", "true") \
    .enableHiveSupport() \
    .getOrCreate()

print("=" * 60)
print("  跨境电商深度决策分析 — ADS表构建")
print("=" * 60)

MYSQL_URL = "jdbc:mysql://hadoop01:3306/bipt_project"
MYSQL_PROPS = {"driver": "com.mysql.cj.jdbc.Driver", "user": "root", "password": "Root@123456"}

def to_mysql(df, table):
    df.write.mode("overwrite").jdbc(MYSQL_URL, table, properties=MYSQL_PROPS)
    print(f"  -> MySQL {table}: {df.count()} rows")

# ---- 加载源数据 ----
sent = spark.table("ads_sentiment_detail")  # 情感明细
prod = spark.table("ads_product_rating")    # 商品评分总览
dwd  = spark.table("dwd_reviews")           # 清洗后明细

# ============================================================
# 表1: ads_feature_country_product — 国家×商品×产品特征ABSA
# ============================================================
print("\n[1/5] 国家×商品×产品特征 三维ABSA矩阵...")

feat = sent.filter(F.col("label1") != "").groupBy(
    "buyer_country", "product_id",
    F.col("label1").alias("feature"),
    F.col("labelValue1").alias("score")
).agg(F.count("*").alias("cnt"))

# 标记正面/负面
feat = feat.withColumn("sentiment_flag",
    F.when(F.col("score").isin("Fast", "Good", "Great"), "positive")
     .when(F.col("score").isin("Poor", "Difficult"), "negative")
     .otherwise("neutral")
)

spark.sql("DROP TABLE IF EXISTS ads_feature_country_product")
feat.write.mode("overwrite").saveAsTable("ads_feature_country_product")
to_mysql(feat, "ads_feature_country_product")

# ============================================================
# 表2: ads_country_product_matrix — 国家×商品评分矩阵(TOP15国家)
# ============================================================
print("\n[2/5] 国别适配度热力矩阵...")

top15 = sent.groupBy("buyer_country").agg(
    F.count("*").alias("total")
).orderBy(F.desc("total")).limit(15)

matrix = sent.join(top15.select("buyer_country"), "buyer_country") \
    .groupBy("buyer_country", "product_id") \
    .agg(
        F.count("*").alias("review_count"),
        F.round(F.avg("star_rating"), 2).alias("avg_star"),
        F.round(F.avg("sentiment_score"), 3).alias("avg_sentiment")
    )

spark.sql("DROP TABLE IF EXISTS ads_country_product_matrix")
matrix.write.mode("overwrite").saveAsTable("ads_country_product_matrix")
to_mysql(matrix, "ads_country_product_matrix")

# ============================================================
# 表3: ads_sku_country_pref — 分国家SKU偏好
# ============================================================
print("\n[3/5] 分国家·分品类 SKU偏好分析...")

top5_countries = spark.sql("""
    SELECT buyer_country FROM (
        SELECT buyer_country, COUNT(*) as c FROM ads_sentiment_detail
        GROUP BY buyer_country ORDER BY c DESC LIMIT 10
    ) t
""")

sku = sent.filter(F.col("sku_info") != "") \
    .join(top5_countries, "buyer_country") \
    .groupBy("buyer_country", "product_id", "sku_info") \
    .agg(
        F.count("*").alias("review_count"),
        F.round(F.avg("star_rating"), 2).alias("avg_star")
    )

spark.sql("DROP TABLE IF EXISTS ads_sku_country_pref")
sku.write.mode("overwrite").saveAsTable("ads_sku_country_pref")
to_mysql(sku, "ads_sku_country_pref")

# ============================================================
# 表4: ads_country_monthly_trend — 时间×国家×商品评分趋势
# ============================================================
print("\n[4/5] 时间×国家×商品 三维趋势分析...")

trend = dwd.groupBy(
    "product_id",
    "buyer_country",
    F.substring("eval_date", 1, 7).alias("month")
).agg(
    F.count("*").alias("review_count"),
    F.round(F.avg("star_rating"), 2).alias("avg_star")
).orderBy("product_id", "buyer_country", "month")

spark.sql("DROP TABLE IF EXISTS ads_country_monthly_trend")
trend.write.mode("overwrite").saveAsTable("ads_country_monthly_trend")
to_mysql(trend, "ads_country_monthly_trend")

# ============================================================
# 表5: ads_feature_time_analysis — 时间×产品特征变化
# ============================================================
print("\n[5/5] 产品特征随时间的变化分析...")

feat_time = sent.filter(F.col("label1") != "") \
    .withColumn("month", F.substring("eval_date", 1, 7)) \
    .groupBy("product_id", F.col("label1").alias("feature"), "month") \
    .agg(
        F.count("*").alias("total"),
        F.sum(F.when(F.col("sentiment_label") == "positive", 1).otherwise(0)).alias("pos_cnt"),
        F.sum(F.when(F.col("sentiment_label") == "negative", 1).otherwise(0)).alias("neg_cnt")
    ).withColumn("pos_rate", F.round(F.col("pos_cnt") * 100.0 / F.col("total"), 1))

spark.sql("DROP TABLE IF EXISTS ads_feature_time_analysis")
feat_time.write.mode("overwrite").saveAsTable("ads_feature_time_analysis")
to_mysql(feat_time, "ads_feature_time_analysis")

# ============================================================
print("\n" + "=" * 60)
print("  5张深度分析表全部完成！")
print("=" * 60)
spark.stop()
