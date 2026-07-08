# 项目总览

> 跨境电商评论情感挖掘与选品决策支持系统 — 昌平champion盛世  
> v3.0 | 2026-07-08

---

## 一、项目简介

基于 AliExpress mtop API 采集 5 品类评论数据，构建"数据采集→大数据存储治理→数据分析计算→数据同步→后端服务接口→前端可视化展示"全链路，输出选品推荐、情感趋势、国家适配度等决策建议。

| 关键指标 | 数值 |
|---|---|
| 原始数据（CSV） | 19,271 条 |
| DWD 清洗后 | 19,248 条（过滤率 0.12%） |
| 覆盖国家 | 135 个（CSV）/ DWD 清洗后收缩 |
| 时间跨度 | 2025-07 ~ 2026-07（13 个月） |
| 分析品类 | 蓝牙耳机/手机壳/LED小夜灯/连衣裙/油壶 |
| 集群节点 | 3 台 CentOS 7，Hadoop HA + YARN 24GB |

## 二、技术架构（七大组件、六大环节）

```
┌──────────────────────────────────────────────────┐
│  数据采集层     Python 爬虫 + MD5 签名 + 断点续爬    │
│  存储治理层     HDFS HA + Hive 四层数仓(ODS→DWD→DWS→ADS)│
│  分析计算层     Spark SQL + VADER 情感 + LDA 主题聚类  │
│  数据同步层     Spark JDBC → MySQL 14 张 ADS 表     │
│  后端服务层     SpringBoot 3.2 + 16 个 REST API     │
│  前端可视层     Vue3 + ECharts 4Tab 大屏            │
└──────────────────────────────────────────────────┘
```

## 三、分析模型

| 方法 | 用途 | 技术 |
|---|---|---|
| VADER 情感分析 | 19,248 条评论逐条打分（compound + 正面/中性/负面标签） | 规则引擎 |
| 选品评分卡 | 5 维度加权排名（评分/好评率/VADER/评论量/国家覆盖） | 加权公式 |
| ABSA 特征分析 | 产品特征×情感标签交叉（关键词 + 平台预标注双源） | 规则提取 |
| 国家适配度矩阵 | TOP15 国家×5 品类评分交叉表 + 热力图 | Spark SQL |
| **LDA 主题模型** | 1,787 条低分评论自动聚类 5 个痛点主题 | **无监督 ML** |
| Pandas/Numpy EDA | 全面描述性统计 + 可视化 | 基础分析 |

## 四、LDA 主题聚类结论

| 主题 | 关键词 | 最大影响品类 | 业务启示 |
|---|---|---|---|
| 尺寸不符 | small, size, smaller | LED灯 (249条) | 标明实际尺寸而非仅图片 |
| 商品损坏 | broken, doesn't work, damaged | 蓝牙耳机 (250条) | 加强包装和品控 |
| 音质/质量差 | poor quality, sound quality | 蓝牙耳机 (250条) | 核心卖点需实地验证 |
| 材质廉价 | cheap, plastic, color | 手机壳 (87条) | 实物图 vs 精修图一致性 |
| 适配错误 | didn't fit, iphone | 手机壳 (84条) | 型号匹配表需及时更新 |

## 五、MR vs Spark 性能对比

| 数据量 | MR on YARN | Spark | 加速比 |
|---|---|---|---|
| 1,000 条 | 22.2s | 4.8s | 4.6× |
| 10,000 条 | 24.9s | 1.0s | 25.8× |
| 19,271 条 | 23.9s | 1.4s | 17.5× |

**结论：** MR 主要开销在 YARN 容器启动（~20s），Spark 首次冷启动后后续计算仅秒级。Hive 管元数据 + Spark 做计算引擎是当前企业湖仓一体架构的最佳实践。

## 六、关键 Bug 解决记录

| # | Bug | 根因 | 方案 |
|---|---|---|---|
| 1 | CSV 换行 → Hive TEXTFILE 行数膨胀 | Hive 不支持 RFC 4180 标准 | Python 全列扁平化 |
| 2 | MapReduce GROUP BY OOM | 3GB VM 内存吃不下复杂聚合 | Spark 替代 MR 计算 |
| 3 | eval_date 全部 NULL | Python 预处理引入列偏移 | Spark multiLine 重读原始 CSV |
| 4 | Spark 找不到 MySQL 驱动 | Spark 不共享 Hive lib | 拷 JDBC jar 到 Spark/jars |
| 5 | Spark 无法解析 HDFS HA mycluster | Spark conf 不含 Hadoop 配置 | 拷 core/hdfs-site.xml 到 Spark/conf |
| 6 | YARN+MR 部署三重障碍 | 用户配置+类路径+XML 损坏 | 完整重写配置+scp 同步 |
| 7 | Sqoop HCatalog 导出 Parquet 卡死 | Sqoop 不原生支持 Parquet | 改用 Spark JDBC |
| 8 | MySQL 8.0 Public Key Retrieval | caching_sha2_password 认证 | JDBC URL 加 allowPublicKeyRetrieval=true |
| 9 | ABSA 特征图部分品类空白 | 速卖通 AI 标签覆盖不均衡 | 前端占位 + 自建关键词标注 + LDA 兜底 |
| 10 | 爬虫 API 翻到最后页循环重复 | 速卖通 API 超出范围后回首页 | 评价 ID 去重 + 连续重复检测 |

## 七、部署

| 场景 | 地址 | 说明 |
|---|---|---|
| 局域网 | `http://192.168.229.101:8080` | 前端内嵌 JAR，一个端口全搞定 |
| 公网备用 | `https://squint-owl-worshiper.ngrok-free.dev` | ngrok 固定域名穿透 |
| GitHub | `https://github.com/siyiliang41-collab/cross-border-review-analysis-` | 全部代码 + 文档 |

## 八、工程化文档

| 文档 | 文件名 |
|---|---|
| 编码规范 | `docs/coding-standards.md` |
| 代码评审记录 | `docs/code-review-record.md` |
| 里程碑计划 | `docs/milestone-plan.md` |
| 项目管理看板 | `docs/project-tracker.md` |
| 团队协作记录 | `docs/team-collaboration-record.md` |
| 运维操作手册 | `docs/operations-guide.md` |
| API 接口清单 | `docs/api-list.md` |
| 项目总览 | `docs/final-summary.md`（本文件） |
