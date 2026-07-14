# 答辩截图与证据清单

> 跨境电商评论情感挖掘与选品决策支持系统 — 昌平champion盛世  
> v5.0 | 2026-07-14

---

## 一、HA 故障切换演示

| 文件名 | 内容 | 用途 |
|---|---|---|
| `HA-初始状态-hadoop01-active` | `hdfs haadmin -getAllServiceState` 初始状态截图 | PPT 演示前 |
| `HA-切换命令成功` | `hdfs haadmin -failover nn1 nn2` 输出 "successful" | PPT 核心证据 |
| `HA-切换后-hadoop02-active` | 切换后 `getAllServiceState` | PPT 切换对比 |
| `HA-切换后文件正常读取` | `hdfs dfs -cat /ha_test.txt` | PPT 零数据丢失证据 |
| `HA-切回hadoop01-active` | 回切后恢复原状 | PPT 可逆可控 |
| `HDFS读写正常` | `hdfs dfs -ls /` + `hdfs dfs -put` | PPT HDFS 可用性 |

这些截图在 `答辩截图汇总/` 目录下。

## 二、数仓 & MySQL 导出

| 文件名 | 内容 | 用途 |
|---|---|---|
| `DWD重建` | `rebuild_dwd.scala` 运行输出，显示 19,248 行 | PPT 数据清洗证据 |
| `DWS+基础ADS重建成功` | `rebuild_all.scala` 月度趋势表输出 | PPT 数仓建模证据 |
| `14张表齐全` | `SHOW TABLES LIKE 'ads_*'` 输出 | PPT 数仓完整性 |
| `13张表全部导出到 MySQL` | `export_mysql.scala` 全部 "OK" 输出 | PPT ETL 证据 |
| `情感挖掘+选品决策完成` | `sentiment_analysis.py` 最后输出 | PPT 情感分析证据 |

这些截图在 `答辩截图汇总/` 目录下。

## 三、v3.0 全量数据

| 文件名 | 内容 | 用途 |
|---|---|---|
| `v3.0全量数据上传成功` | CSV 推送到 HDFS /user/root/ 的 `-ls` 输出 | PPT 数据增量证据 |
| `爬虫完成输出` | `完成！本次采集 19271 条` | PPT 采集能力证据 |

## 四、MR vs Spark 性能对比

| 文件名 | 内容 | 用途 |
|---|---|---|
| `MR 1k 完成` | MR WordCount 1k `completed successfully` + time | PPT 性能对比 |
| `MR 10k 完成` | MR WordCount 10k time | PPT 性能对比 |
| `MR full 完成` | MR WordCount 全量 time | PPT 性能对比 |
| `Spark 三组完成` | Spark WordCount 三组耗时 | PPT 性能对比 |
| `charts/mr_vs_spark.png` | 并排柱状图 + 加速比折线 | PPT 核心图 |
| `YARN 3节点24GB` | YARN Web UI 截图 | PPT 集群规模 |

## 五、LDA 主题模型

| 文件名 | 内容 | 用途 |
|---|---|---|
| `LDA 完整输出` | `lda_topic_model.py` 全部终端输出 | PPT ML 算法证据 |
| `charts/lda_topics.png` | 5主题词频 + 品类痛点分布 | PPT 核心图 |

## 六、Pandas/Numpy EDA

| 文件名 | 内容 | 用途 |
|---|---|---|
| `Pandas EDA 终端输出` | `pandas_eda.py` 全部统计输出 | PPT 基础分析证据 |
| `charts/pandas_eda_charts.png` | 4合1：评分分布/品类柱状/月度趋势/星评对比 | PPT 核心图 |

## 七、前端大屏（四 Tab — v4.0 重构）

| 文件名 | 内容 | 用途 |
|---|---|---|
| `前端-数据概览Tab` | 趋势折线/雷达/热力/KMeans矢量散点/选品排名/情感堆叠 | PPT 可视化 |
| `前端-产品洞察Tab` | ABSA特征/月度趋势/情感环形图（跟选品切换） | PPT 可视化 |
| `前端-市场洞察Tab` | TOP5排名卡片+国家详情+预测线+LDA兜底风险 | PPT 可视化 |
| `前端-数据质量Tab` | 概览/清洗/月度/国家/品类/结论 | PPT 可视化 |
| `前端-数据管理Tab` | 评论增删改查/分页/搜索/登录认证 | PPT 可视化 |
| `F12 Console 无报错` | 控制台截图，证明全链路无异常 | PPT 联调成功 |

## 八、部署验证

| 文件名 | 内容 | 用途 |
|---|---|---|
| `后端curl验证` | `curl http://localhost:8080/api/overview` 返回 JSON | PPT 后端可用 |
| `局域网访问` | `http://192.168.229.101:8080` 浏览器截图 | PPT 局域网部署 |
| `公网访问` | `https://squint-owl-worshiper.ngrok-free.dev` 截图 | PPT 公网部署 |

## 九、尚未截图的（答辩前补）

| 需要截图 | 说明 |
|---|---|
| YARN Web UI (`http://192.168.229.103:8088`) | 3个 Active Nodes + Total Memory 24GB |
| HDFS NameNode Web UI (`http://192.168.229.101:9870`) | Active NameNode + 3 DataNodes |
| 前端 5 Tab 逐张截图 | 数据概览/产品洞察/市场洞察/数据质量/数据管理 |
| ZooKeeper 三节点 status | Leader/Follower 状态 |
| 登录/注册页面 | AuthPage 界面截图 |
| 数据管理 CRUD 操作 | 增删改查弹窗截图 |

## 十、所有图表产物

| 文件路径 | 内容 |
|---|---|
| `charts/pandas_eda_charts.png` | Pandas EDA 4合1图 |
| `charts/mr_vs_spark.png` | MR vs Spark 对比图 |
| `charts/lda_topics.png` | LDA 5主题词频 + 痛点分布 |
| `charts/kmeans_country_clusters.png` | KMeans PCA散点 + 4类市场卡片 |
| `charts/consistency_analysis.png` | 评分与情感一致性分析三图 |
