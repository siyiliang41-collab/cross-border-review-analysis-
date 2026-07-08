import org.apache.spark.sql.SaveMode

// DWS
spark.sql("DROP TABLE IF EXISTS dws_reviews")
spark.sql("CREATE TABLE dws_reviews AS SELECT product_id, buyer_country, COUNT(*) AS review_count, ROUND(AVG(star_rating),2) AS avg_star FROM dwd_reviews GROUP BY product_id, buyer_country")

// ADS
spark.sql("DROP TABLE IF EXISTS ads_product_rating")
spark.sql("CREATE TABLE ads_product_rating AS SELECT product_id, COUNT(*) AS total_reviews, ROUND(AVG(star_rating),2) AS avg_star FROM dwd_reviews GROUP BY product_id")

spark.sql("DROP TABLE IF EXISTS ads_country_top15")
spark.sql("CREATE TABLE ads_country_top15 AS SELECT buyer_country, COUNT(*) AS cnt, ROUND(AVG(star_rating),2) AS avg_star FROM dwd_reviews GROUP BY buyer_country ORDER BY cnt DESC LIMIT 15")

spark.sql("DROP TABLE IF EXISTS ads_monthly_trend")
spark.sql("CREATE TABLE ads_monthly_trend AS SELECT SUBSTR(eval_date,1,7) AS m, COUNT(*) AS cnt, ROUND(AVG(star_rating),2) AS avg FROM dwd_reviews GROUP BY SUBSTR(eval_date,1,7) ORDER BY m")

spark.sql("DROP TABLE IF EXISTS ads_logistics")
spark.sql("CREATE TABLE ads_logistics AS SELECT logistics, COUNT(*) AS cnt, ROUND(AVG(star_rating),2) AS avg FROM dwd_reviews WHERE logistics!='' GROUP BY logistics")

spark.sql("DROP TABLE IF EXISTS ads_image_followup")
spark.sql("CREATE TABLE ads_image_followup AS SELECT has_image, has_follow_up, COUNT(*) AS cnt, ROUND(AVG(star_rating),2) AS avg FROM dwd_reviews GROUP BY has_image, has_follow_up")

spark.sql("DROP TABLE IF EXISTS ads_sku_analysis")
spark.sql("CREATE TABLE ads_sku_analysis AS SELECT product_id, sku_info, COUNT(*) AS cnt, ROUND(AVG(star_rating),2) AS avg FROM dwd_reviews WHERE sku_info!='' GROUP BY product_id, sku_info")

// show monthly trend
spark.table("ads_monthly_trend").show(20)

// export to MySQL
val props = new java.util.Properties()
props.setProperty("driver","com.mysql.cj.jdbc.Driver")
props.setProperty("user","root")
props.setProperty("password","Root@123456")
val url = "jdbc:mysql://hadoop01:3306/bipt_project"
spark.table("ads_product_rating").write.mode(SaveMode.Overwrite).jdbc(url,"ads_product_rating",props)
spark.table("ads_country_top15").write.mode(SaveMode.Overwrite).jdbc(url,"ads_country_top15",props)
spark.table("ads_monthly_trend").write.mode(SaveMode.Overwrite).jdbc(url,"ads_monthly_trend",props)
spark.table("ads_logistics").write.mode(SaveMode.Overwrite).jdbc(url,"ads_logistics",props)
spark.table("ads_image_followup").write.mode(SaveMode.Overwrite).jdbc(url,"ads_image_followup",props)
spark.table("ads_sku_analysis").write.mode(SaveMode.Overwrite).jdbc(url,"ads_sku_analysis",props)

println("ALL EXPORTED TO MySQL")
