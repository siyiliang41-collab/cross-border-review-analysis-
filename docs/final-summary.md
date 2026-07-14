# 项目总览

> 跨境电商评论情感挖掘与选品决策支持系统 — 昌平champion盛世  
> v5.0 | 2026-07-14

---

## 一、项目简介

基于 AliExpress mtop API 采集 5 品类评论数据，构建"数据采集→大数据存储治理→数据分析计算→数据同步→后端服务接口→前端可视化展示"全链路，输出选品推荐、情感趋势、国家适配度等决策建议。

| 关键指标 | 数值 |
|---|---|
| 原始数据（CSV） | 19,271 条（127 个国家） |
| DWD 清洗后 | 19,248 条（过滤率 0.12%，102 个国家 ≥3 条评论） |
| 时间跨度 | 2025-07 ~ 2026-07（13 个月） |
| 分析品类 | 蓝牙耳机/手机壳/LED小夜灯/连衣裙/油壶 |
| 集群节点 | 3 台 CentOS 7，Hadoop HA + YARN 24GB |
| MySQL 表 | 15 张（13 ADS + bipt_review + users） |
| API 端点 | 25 个（17 业务 + 2 认证 + 6 CRUD） |
| Git commits | 68 条规范提交 |
| Bug 记录 | 12 个完整根因分析 |

## 二、技术架构（六层全链路）

```
┌──────────────────────────────────────────────────┐
│  数据采集层     Python 爬虫 v3 + MD5 签名 + 断点续爬    │
│  存储治理层     HDFS HA + Hive 四层数仓(ODS→DWD→DWS→ADS, 9表)│
│  分析计算层     Spark SQL + VADER 情感 + LDA 主题聚类 + KMeans  │
│  数据同步层     Spark JDBC → MySQL 15 张表          │
│  后端服务层     SpringBoot 3.2 + MyBatis Plus + JWT + 25 API │
│  前端可视层     Vue3 + ECharts 5Tab 大屏 + Element Plus CRUD  │
└──────────────────────────────────────────────────┘
```

## 三、分析模型

| 方法 | 用途 | 技术 |
|---|---|---|
| VADER 情感分析 | 19,248 条评论逐条打分（compound ≥0.05 正面 / ≤-0.05 负面） | 规则引擎 |
| 选品评分卡 | 5 维度加权排名（星评/好评率/VADER/评论量/国家覆盖） | 加权公式 |
| ABSA 特征分析 | 产品特征×情感标签交叉（速卖通标签 + 自建关键词词典双源） | 规则提取 |
| 国家适配度矩阵 | TOP15 国家×5 品类评分交叉表 + 热力图 | Spark SQL |
| **LDA 主题模型** | 1,787 条低分评论（star≤2）自动聚类 5 个痛点主题 | **无监督 ML** |
| **KMeans 国家分群** | 102 个国家聚为 4 类消费市场类型（Star/Box/Seed/Zoom） | **无监督 ML** |
| **时序预测** | 纯前端线性回归，预测下月评分趋势 | 线性回归 |
| **评分情感一致性** | 7,464 条星评-情感交叉校验，异常率 5.6% | 相关性检验 |
| Pandas/Numpy EDA | 7 大模块描述性统计 + 4 张可视化图 | 基础分析 |

## 四、LDA 主题聚类结论

| 主题 | 关键词 | 最大影响品类 | 业务启示 |
|---|---|---|---|
| 尺寸不符 | small, size, smaller | LED灯 (249条) | 标明实际尺寸而非仅图片 |
| 商品损坏 | broken, doesn't work, damaged | 蓝牙耳机 (250条) | 加强包装和品控 |
| 音质/质量差 | poor quality, sound quality | 蓝牙耳机 (250条) | 核心卖点需实地验证 |
| 材质廉价 | cheap, plastic, color | 手机壳 (87条) | 实物图 vs 精修图一致性 |
| 适配错误 | didn't fit, iphone | 手机壳 (84条) | 型号匹配表需及时更新 |

> 参数: CountVectorizer(max_features=5000, max_df=0.7, min_df=5, ngram 1-2), LDA(n=5, online, max_iter=30), 困惑度 388.5

## 五、MR vs Spark 性能对比（同台 YARN 竞技）

| 数据量 | MR on YARN | Spark on YARN | 加速比 |
|---|---|---|---|
| 1,000 条 | 19.9s | 2.2s | 9.0× |
| 10,000 条 | 20.8s | 1.7s | 12.2× |
| 19,271 条 | 21.0s | 1.7s | 12.4× |

**结论：** MR 主要开销在 YARN 容器启动（~20s），数据增大几乎不增耗时。Spark on YARN 占用仅 1.7~2.2s，同一集群同一数据同一任务，加速 9~12 倍。Hive 管元数据 + Spark 做计算引擎是当前企业湖仓一体架构的最佳实践。

## 六、评分与情感一致性分析

| 指标 | 数值 |
|---|---|
| 有效评论（含英文文本） | 7,464 条 |
| 类型A「高星低情感」(star≥4, compound<-0.2) | 199 条 (2.7%) — 疑似刷单 |
| 类型B「低星高情感」(star≤2, compound>0.3) | 219 条 (2.9%) — 翻译偏差 |
| 正常率 | 94.4% |
| Spearman 相关系数 | 星评与情感呈中等偏强正相关 |

**结论：** 仅 5.6% 的评论存在评分与情感不一致，数据整体可靠。详见 `charts/consistency_analysis.png`。

## 七、KMeans 国家分群

| 聚类 | 国家数 | 均星评 | 均评论数 | 策略建议 |
|---|---|---|---|---|
| 成熟高价值市场 (Star) | 11 | 4.31 | 1,293 | 重点投入，品牌化运营 |
| 价格敏感大市场 (Box) | 60 | 4.21 | 80 | 价格/物流竞争主导 |
| 潜力精品市场 (Seed) | 25 | 4.56 | 8 | 适合新品试水，低风险 |
| 长尾探索市场 (Zoom) | 6 | 3.35 | 6 | 暂不推荐，性价比较低 |

> 特征: 评论数/平均星评/星评标准差/带图率/追评率/品类数，StandardScaler + PCA(55.1%可解释方差) + KMeans(K=4)。前端以 ECharts 矢量散点图呈现。

## 八、前端大屏

5 个 Tab 结构（v5.0）：

| Tab | 粒度 | 图表 |
|---|---|---|
| 数据概览 | 全品类 | 趋势折线 / 雷达图 / 热力图 / KMeans散点 / 选品排名 / 情感堆叠 |
| 产品洞察 | 单品 | ABSA特征 / 月度趋势 / 情感环形图（跟随顶栏选品切换） |
| 市场洞察 | 国家 | TOP5排名卡片 / 国家深度详情 / 趋势预测 / SKU偏好 |
| 数据质量 | 全品类 | 数据概览 / 清洗统计 / 月度分布 / 国家覆盖 / 品类画像 |
| 数据管理 | 全品类 | 评论增删改查 / 分页浏览 / 关键词搜索 / 品类国家筛选 |

- **布局：** 2+2+1 卡片布局（两行双图 + 全宽图），左侧深色导航 + 右侧悬浮指标卡
- **API 路径：** 相对路径 `/api`，嵌入式部署前后端同源，无跨域问题
- **KMeans 图：** ECharts 矢量散点图，102 国 PC1/PC2 坐标 + 气泡大小 = 评论规模
- **预测线：** 纯前端 `lrPredict()` 线性回归，最小二乘法，红色虚线 + 菱形
- **LDA 兜底：** 无负面特征的国家自动引用全品类 LDA 结论
- **认证：** AuthPage 登录/注册页，localStorage 存 JWT，Axios 拦截器自动附带 token

## 九、关键 Bug 解决记录

| # | Bug | 根因 | 方案 |
|---|---|---|---|
| 1 | CSV 换行 → Hive TEXTFILE 行数膨胀(18001) | Hive 不支持 RFC 4180 标准 | Python 全列扁平化 |
| 2 | MapReduce GROUP BY OOM | 3GB VM 内存吃不下复杂聚合 | Spark 替代 MR 计算 |
| 3 | eval_date 全部 NULL | Python 预处理引入列偏移 | Spark multiLine 重读原始 CSV |
| 4 | Spark 找不到 MySQL 驱动 | Spark 不共享 Hive lib | 拷 JDBC jar 到 Spark/jars |
| 5 | Spark 无法解析 HDFS HA mycluster | Spark conf 不含 Hadoop 配置 | 拷 core/hdfs-site.xml 到 Spark/conf |
| 6 | YARN+MR 部署三重障碍 | 用户配置+类路径+XML 损坏 | 完整重写配置+scp 同步 |
| 7 | Sqoop HCatalog 导出 Parquet 卡死 | Sqoop 不原生支持 Parquet | 改用 Spark JDBC |
| 8 | MySQL 8.0 Public Key Retrieval | caching_sha2_password 认证 | JDBC URL 加 allowPublicKeyRetrieval=true |
| 9 | ABSA 特征图部分品类空白 | 速卖通 AI 标签覆盖不均衡 | 自建关键词标注(tag_features.py) + LDA 兜底 |
| 10 | 爬虫 API 翻到最后页循环重复 | 速卖通 API 超出范围后回首页 | 评价 ID 去重 + 连续重复检测 |
| 11 | CRUD 前端卡顿+颜色丢失 | 图标全量注册 2.3MB + Router watch 竞态 | 去全局图标+去 Router+回滚 onMounted |
| 12 | evaluationId 17 位精度丢失删不了 | JS Number 最大 16 位安全整数 | @JsonSerialize(ToStringSerializer) + @PathVariable String |

## 十、用户认证（v5.0 新增）

| 端点 | 说明 | 权限 |
|------|------|------|
| POST `/api/auth/login` | 用户登录 → 返回 JWT token | 公开 |
| POST `/api/auth/register` | 用户注册 → 默认 role=user | 公开 |

- **管理员** (admin/admin123)：`/api/crud/**` POST/PUT/DELETE 可操作
- **普通用户**（自行注册）：仅 GET 可查看，增删改按钮不显示
- 技术: JWT (jjwt 0.12.6, 24h 过期) + BCrypt (cost=12) + Spring Interceptor（仅拦截 CRUD 写操作）
- 数据管理 Tab 对普通用户可见（只读），增删改按钮 `v-if="canEdit"` 控制

## 十一、MySQL 数据库表清单（15 张）

### ADS 业务表（13 张）

| 表名 | 说明 | 构建脚本 |
|---|---|---|
| `ads_product_rating` | 商品评分汇总 | rebuild_all.scala |
| `ads_country_top15` | TOP15 国家评分排名 | rebuild_all.scala |
| `ads_monthly_trend` | 月度评论量 & 评分趋势 | rebuild_all.scala |
| `ads_logistics` | 物流方式满意度 | rebuild_all.scala |
| `ads_image_followup` | 带图/追评行为统计 | rebuild_all.scala |
| `ads_sku_analysis` | SKU 分析 | rebuild_all.scala |
| `ads_sentiment_product` | 各品类情感正/中/负面率 | sentiment_analysis.py |
| `ads_product_scorecard` | 选品评分卡 | sentiment_analysis.py |
| `ads_country_product_matrix` | 国家×商品适配度矩阵 | build_deep_ads.py |
| `ads_feature_country_product` | 产品特征 ABSA（国家×商品） | build_deep_ads.py + tag_features.py |
| `ads_sku_country_pref` | 国家×商品 SKU 偏好 | build_deep_ads.py |
| `ads_country_monthly_trend` | 国家×商品月度趋势 | build_deep_ads.py |
| `ads_feature_time_analysis` | 产品特征月度情感走势（44 行） | build_deep_ads.py |

### v5.0 新增（2 张）

| 表名 | 说明 |
|---|---|
| `bipt_review` | 评论个体数据（22 字段，19,271 条，CRUD 管理） |
| `users` | 用户认证表（id/username/password_hash/role/created_at） |

> **注意：** `ads_sentiment_detail`（19,248 条逐条情感标注）仅在 Hive 中，未导出到 MySQL。

## 十二、部署

| 场景 | 地址 | 说明 |
|---|---|---|
| 局域网 | `http://192.168.229.101:8080` | 前端内嵌 JAR，一个端口全搞定 |
| 公网备用 | `https://squint-owl-worshiper.ngrok-free.dev` | ngrok 固定域名穿透（首次需点 Visit Site） |
| 源代码 | `https://github.com/siyiliang41-collab/cross-border-review-analysis-` | 全部代码 + 文档（仅 GitHub，无 Gitee） |

> **注意：** 答辩优先用局域网地址。ngrok 免费版有真人验证和限流。

## 十三、工程化文档

| 文档 | 文件名 |
|---|---|
| 编码规范 | `docs/coding-standards.md` |
| 代码评审记录 | `docs/code-review-record.md`（36 项） |
| 里程碑计划 | `docs/milestone-plan.md`（M1~M5） |
| 项目管理看板 | `docs/project-tracker.md`（46 项任务） |
| 团队协作记录 | `docs/team-collaboration-record.md` |
| 运维操作手册 | `docs/operations-guide.md` |
| API 接口清单 | `docs/api-list.md` |
| 项目总览 | `docs/final-summary.md`（本文件） |
| 答辩截图指南 | `docs/screenshot-guide.md` |
