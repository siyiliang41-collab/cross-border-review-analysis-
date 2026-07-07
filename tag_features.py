# -*- coding: utf-8 -*-
"""
文件名：tag_features.py
功能：基于评论关键词匹配，为每个品类标注5个产品特征
     补全手机壳/LED灯/油壶的缺失特征，蓝牙耳机和连衣裙各补2个
作者：梁思怡
创建日期：2026-07-07
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, explode, count as spark_count, sum as spark_sum
from pyspark.sql.types import ArrayType, StructType, StructField, StringType

spark = SparkSession.builder \
    .appName("FeatureTagging") \
    .config("spark.sql.adaptive.enabled", "true") \
    .enableHiveSupport() \
    .getOrCreate()

# ============================================================
# 关键词词典 — 每个品类5个特征，正/负面关键词
# ============================================================
FEATURE_DICT = {
    # 蓝牙耳机：原有3个 + 补续航、舒适度
    "3256808363596774": [
        ("音质", ["sound quality", "sound", "audio", "bass", "clear sound", "loud", "noise cancelling"],
         ["bad sound", "poor sound", "noisy", "distorted", "static"]),
        ("耐用", ["durable", "sturdy", "well made", "quality build", "lasting", "solid"],
         ["broke", "broken", "cheap build", "fell apart", "stopped working"]),
        ("易用性", ["easy to use", "user friendly", "pairing", "bluetooth", "connect", "simple", "touch control"],
         ["hard to pair", "difficult to connect", "complicated", "not connecting"]),
        ("续航", ["battery", "charge", "long lasting", "hours of", "battery life", "playtime", "fast charge"],
         ["battery drain", "short battery", "die quick", "charge often", "bad battery", "dead"]),
        ("舒适度", ["comfortable", "comfort", "fit well", "lightweight", "ear", "soft eartip", "ergonomic", "wear"],
         ["uncomfortable", "painful", "hurts", "heavy", "fall out", "loose", "sore"]),
    ],
    # 手机壳：5个新特征
    "3256807406290815": [
        ("保护性", ["protect", "protection", "shockproof", "drop", "military grade", "safe", "rugged", "armor"],
         ["no protection", "cracked", "shattered", "damage", "dent", "scratched screen"]),
        ("贴合度", ["fit", "perfect fit", "snug", "precise", "exact cut", "fits perfectly", "thin fit", "slim fit"],
         ["loose", "doesn't fit", "too tight", "gap", "not align", "bulky", "hard to put"]),
        ("手感", ["feel", "grip", "smooth", "soft touch", "texture", "matte", "hand feel", "non slip", "comfortable hold"],
         ["slippery", "rough", "sticky", "bad grip", "slides"]),
        ("外观", ["look", "beautiful", "nice", "color", "design", "pretty", "clear", "transparent", "cute", "elegant", "stylish"],
         ["ugly", "faded", "yellow", "scratch", "cheap looking", "discolored"]),
        ("耐用", ["durable", "quality", "sturdy", "strong", "well made", "good quality", "lasting", "doesn't break"],
         ["broke", "broken", "cheap", "poor quality", "tear", "worn", "flimsy", "fell apart"]),
    ],
    # LED小夜灯：5个新特征
    "3256807087680846": [
        ("亮度", ["bright", "brightness", "good light", "bright enough", "illuminate", "well lit", "powerful light"],
         ["dim", "too bright", "faint", "barely see", "not bright", "weak", "blinding"]),
        ("光色柔和", ["warm", "soft light", "gentle", "color change", "eye friendly", "cozy", "ambient", "romantic", "warm glow"],
         ["harsh", "too white", "cold light", "glare", "uncomfortable light", "too blue"]),
        ("外观设计", ["design", "cute", "beautiful", "nice", "pretty", "shape", "unique", "creative", "adorable", "lovely"],
         ["ugly", "cheap looking", "bulky", "unattractive", "plastic"]),
        ("易安装", ["easy to install", "easy setup", "stick", "adhesive", "magnetic", "plug in", "simple install", "just stick"],
         ["hard to install", "difficult", "won't stick", "fell off", "not staying", "adhesive fail"]),
        ("耐用", ["durable", "quality", "long lasting", "reliable", "well made", "good material", "sturdy"],
         ["broke", "stopped working", "cheap", "flimsy", "dead on arrival", "defective"]),
    ],
    # 连衣裙：原有3个 + 补面料舒适、款式设计
    "3256807145227935": [
        ("合身度", ["fit", "perfect fit", "true to size", "flattering", "fits well", "measurement", "size chart"],
         ["too small", "too big", "doesn't fit", "tight", "loose", "wrong size", "runs small", "runs large"]),
        ("性价比", ["value", "price", "worth", "affordable", "cheap", "good deal", "bargain", "great price"],
         ["expensive", "overpriced", "not worth", "waste of money", "rip off"]),
        ("质量", ["quality", "well made", "good", "finish", "detail", "craftsmanship", "stitching", "sewn"],
         ["poor quality", "bad quality", "cheap material", "flawed", "not as described", "defect"]),
        ("面料舒适", ["fabric", "material", "comfortable", "soft", "cotton", "breathable", "stretchy", "lightweight", "silky", "smooth", "flowy"],
         ["itchy", "scratchy", "thin", "see through", "stiff", "uncomfortable", "rough", "static"]),
        ("款式设计", ["style", "design", "beautiful", "elegant", "fashion", "pretty", "pattern", "vintage", "classy", "gorgeous", "stunning"],
         ["ugly", "outdated", "boring", "not like picture", "plain", "different from photo"]),
    ],
    # 油壶：5个新特征
    "3256805677493085": [
        ("密封性", ["seal", "no leak", "doesn't leak", "tight cap", "leak proof", "airtight", "secure lid", "no spill"],
         ["leaking", "spill", "loose cap", "not tight", "drips", "messy", "leaks everywhere"]),
        ("容量大小", ["size", "capacity", "ml", "big", "large", "enough", "holds", "bottle", "500ml", "good size"],
         ["too small", "too big", "not enough", "tiny", "smaller than"]),
        ("材质质感", ["glass", "stainless", "material", "quality", "sturdy", "thick", "solid", "durable", "heavy duty"],
         ["thin glass", "flimsy", "cheap plastic", "fragile", "crack", "broke easily"]),
        ("易清洁", ["clean", "wash", "easy to clean", "dishwasher", "rinse", "wipe", "hygienic"],
         ["hard to clean", "difficult to wash", "stain", "dirty", "oily residue", "build up"]),
        ("出油控制", ["pour", "flow", "control", "drip", "nozzle", "spout", "dispense", "even", "smooth pour", "steady"],
         ["too fast", "too slow", "clog", "blocked", "uneven", "spill", "mess", "drips"]),
    ],
}

# 广播词典到所有executor
bc_dict = spark.sparkContext.broadcast(FEATURE_DICT)

# ============================================================
# UDF: 扫描评论文本，返回匹配到的特征列表
# ============================================================
def tag_features(text, product_id):
    """根据关键词匹配，返回该评论涉及的特征+情感"""
    if not text or product_id not in bc_dict.value:
        return []
    text_lower = str(text).lower()
    results = []
    for (feature_cn, pos_kw, neg_kw) in bc_dict.value[product_id]:
        is_positive = any(kw in text_lower for kw in pos_kw)
        is_negative = any(kw in text_lower for kw in neg_kw)
        if is_positive or is_negative:
            # 正面优先：如果同时匹配正负面（如 seal vs leak），取正面
            sentiment = "positive" if is_positive else "negative"
            score = "Good" if is_positive else "Poor"
            results.append({"feature": feature_cn, "sentiment": sentiment, "score": score})
    return results

tag_schema = ArrayType(StructType([
    StructField("feature", StringType()),
    StructField("sentiment", StringType()),
    StructField("score", StringType()),
]))
tag_udf = udf(tag_features, tag_schema)

# ============================================================
# 主流程
# ============================================================

print("=" * 60)
print("  产品特征关键词标注 — 每个品类5个特征")
print("=" * 60)

# ① 加载评论并标注
print("\n[1/5] 扫描评论，匹配关键词词典...")
dwd = spark.table("dwd_reviews")
tagged = dwd.withColumn("features", tag_udf(col("feedback"), col("product_id")))

# ② 展开为一行一特征
print("[2/5] 展开标注结果...")
expanded = tagged.select(
    col("product_id"),
    col("buyer_country"),
    col("eval_date"),
    col("star_rating"),
    explode(col("features")).alias("feat")
).select(
    "product_id", "buyer_country", "eval_date", "star_rating",
    col("feat.feature").alias("label1"),
    col("feat.score").alias("labelValue1"),
    col("feat.sentiment").alias("sentiment_flag"),
)

# ③ 聚合统计
print("[3/5] 聚合特征统计...")
new_tagged = expanded.groupBy(
    "buyer_country", "product_id", "label1", "labelValue1", "sentiment_flag"
).agg(spark_count("*").alias("cnt"))

# ④ 与旧表合并（保留旧标签 + 追加新标签）
print("[4/5] 合并到 ads_feature_country_product...")

# 检查旧表是否存在
from pyspark.sql.utils import AnalysisException
try:
    old = spark.table("ads_feature_country_product") \
        .select(col("buyer_country"), col("product_id"),
                col("feature"), col("score"), col("sentiment_flag"), col("cnt"))
    has_old = True
except AnalysisException:
    print("  旧表不存在，将直接创建新表")
    has_old = False

# 新标注对齐列名
new_aligned = new_tagged.select(
    col("buyer_country"),
    col("product_id"),
    col("label1").alias("feature"),
    col("labelValue1").alias("score"),
    col("sentiment_flag"),
    col("cnt"),
)

# 合并：按 (buyer_country, product_id, feature, score) 去重求和
if has_old:
    merged = old.union(new_aligned).groupBy(
        "buyer_country", "product_id", "feature", "score", "sentiment_flag"
    ).agg(spark_sum("cnt").alias("cnt"))
else:
    merged = new_aligned

# 覆盖写
spark.sql("DROP TABLE IF EXISTS ads_feature_country_product")
merged.write.mode("overwrite").saveAsTable("ads_feature_country_product")

total = merged.count()
print(f"  总特征记录: {total} 条")

# ⑤ 导出MySQL
print("[5/5] 导出到 MySQL...")
MYSQL_URL = "jdbc:mysql://hadoop01:3306/bipt_project"
MYSQL_PROPS = {"driver": "com.mysql.cj.jdbc.Driver", "user": "root", "password": "Root@123456"}
merged.write.mode("overwrite").jdbc(MYSQL_URL, "ads_feature_country_product", properties=MYSQL_PROPS)

# 打印各品类特征覆盖统计
print("\n各品类特征覆盖情况:")
product_names = {
    "3256808363596774": "蓝牙耳机", "3256807406290815": "手机壳",
    "3256807087680846": "LED小夜灯", "3256807145227935": "连衣裙",
    "3256805677493085": "油壶",
}
merged.groupBy("product_id", "feature").agg(spark_count("cnt").alias("mention_count")) \
    .orderBy("product_id", "feature") \
    .collect()  # 触发计算但不打印

for pid, pname in product_names.items():
    features = merged.filter(col("product_id") == pid).select("feature").distinct().collect()
    print(f"  {pname}: {len(features)} 个特征 — {', '.join([f.feature for f in features])}")

print("\n" + "=" * 60)
print("  特征标注完成！5个品类各5个特征，前端ABSA图应该有数据了")
print("=" * 60)
spark.stop()
