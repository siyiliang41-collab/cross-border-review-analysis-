import org.apache.spark.sql.SaveMode
val props = new java.util.Properties()
props.setProperty("driver","com.mysql.cj.jdbc.Driver")
props.setProperty("user","root")
props.setProperty("password","Root@123456")
val url = "jdbc:mysql://hadoop01:3306/bipt_project"
val tables = Seq("ads_product_rating","ads_country_top15","ads_monthly_trend","ads_logistics","ads_image_followup","ads_sku_analysis","ads_sentiment_product","ads_product_scorecard","ads_country_product_matrix","ads_feature_country_product","ads_country_monthly_trend","ads_feature_time_analysis","ads_sku_country_pref")
tables.foreach { t =>
  println(s"Exporting $t ...")
  spark.table(t).write.mode(SaveMode.Overwrite).jdbc(url, t, props)
  println(s"$t OK")
}
println("ALL EXPORTED")
System.exit(0)
