# -*- coding: utf-8 -*-
"""情感挖掘 + 选品评分卡 - 纯PySpark"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, avg, count, sum as spark_sum
from pyspark.sql.functions import round as spark_round, get_json_object, lit
from pyspark.sql.types import StringType, DoubleType
import json

spark = SparkSession.builder \
    .appName("SentimentAnalysis") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.pyspark.python", "/usr/bin/python3") \
    .config("spark.pyspark.driver.python", "/usr/bin/python3") \
    .enableHiveSupport() \
    .getOrCreate()

print("=" * 60)
print("  跨境电商评论情感挖掘 + 选品决策支持系统")
print("=" * 60)

# ---- UDF: VADER情感分析 ----
def analyze_sentiment(text):
    if not text or len(str(text)) < 5:
        return json.dumps({"compound": 0.0, "label": "neutral"})
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    scores = SentimentIntensityAnalyzer().polarity_scores(str(text))
    c = scores['compound']
    if c >= 0.05:
        label = "positive"
    elif c <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    return json.dumps({"compound": round(float(c), 3), "label": label})

sentiment_udf = udf(analyze_sentiment, StringType())

# ---- 步骤1: 情感标注 ----
print("\n[1/4] 对16,972条评论进行VADER情感分析...")
df = spark.table("dwd_reviews")
sent_df = df.withColumn("sentiment_json", sentiment_udf(col("feedback_translated")))
sent_df = sent_df.select(
    "*",
    get_json_object(col("sentiment_json"), "$.compound").cast(DoubleType()).alias("sentiment_score"),
    get_json_object(col("sentiment_json"), "$.label").alias("sentiment_label")
).drop("sentiment_json")

sent_df.write.mode("overwrite").saveAsTable("ads_sentiment_detail")
print(f"   OK: {spark.table('ads_sentiment_detail').count()} 条已完成情感标注")

# ---- 步骤2: 商品情感汇总 ----
print("\n[2/4] 生成商品情感汇总表...")
spark.sql("DROP TABLE IF EXISTS ads_sentiment_product")
spark.sql("""
CREATE TABLE ads_sentiment_product AS
SELECT product_id,
       COUNT(*) AS total,
       ROUND(AVG(sentiment_score), 3) AS avg_sentiment,
       SUM(CASE WHEN sentiment_label='positive' THEN 1 ELSE 0 END) AS pos_cnt,
       SUM(CASE WHEN sentiment_label='neutral' THEN 1 ELSE 0 END) AS neu_cnt,
       SUM(CASE WHEN sentiment_label='negative' THEN 1 ELSE 0 END) AS neg_cnt,
       ROUND(SUM(CASE WHEN sentiment_label='positive' THEN 1 ELSE 0 END)*100.0/COUNT(*), 1) AS pos_rate
FROM ads_sentiment_detail GROUP BY product_id
""")
spark.table("ads_sentiment_product").show(5, False)

# ---- 步骤3: 选品综合评分卡 ----
print("\n[3/4] 计算选品推荐指数...")
max_cnt = spark.sql("SELECT MAX(total) AS m FROM ads_sentiment_product").collect()[0].m

spark.sql("DROP TABLE IF EXISTS ads_product_scorecard")
spark.sql(f"""
CREATE TABLE ads_product_scorecard AS
SELECT
    p.product_id,
    ROUND(p.avg_star, 2) AS star_score,
    ROUND(s.pos_rate, 1) AS sentiment_pos_rate,
    ROUND(s.avg_sentiment, 3) AS avg_sentiment,
    p.total_reviews,
    ROUND(
        p.avg_star * 6.0 +
        s.pos_rate * 0.25 +
        s.avg_sentiment * 12.0 +
        s.total * 100.0 / {max_cnt} * 0.15,
    1) AS recommendation_score
FROM ads_product_rating p
JOIN ads_sentiment_product s ON p.product_id = s.product_id
ORDER BY recommendation_score DESC
""")

print("\n=== 选品推荐排名 ===")
spark.table("ads_product_scorecard").show(5, False)

# ---- 步骤4: 导出MySQL ----
print("\n[4/4] 导出到MySQL bipt_project...")
props = {"driver": "com.mysql.cj.jdbc.Driver", "user": "root", "password": "Root@123456"}
url = "jdbc:mysql://hadoop01:3306/bipt_project"

spark.table("ads_sentiment_product").write.mode("overwrite").option("driver","com.mysql.cj.jdbc.Driver") \
    .jdbc(url, "ads_sentiment_product", properties=props)
spark.table("ads_product_scorecard").write.mode("overwrite").option("driver","com.mysql.cj.jdbc.Driver") \
    .jdbc(url, "ads_product_scorecard", properties=props)

print("\n" + "=" * 60)
print("  情感挖掘 + 选品决策 全部完成！")
print("=" * 60)
spark.stop()
