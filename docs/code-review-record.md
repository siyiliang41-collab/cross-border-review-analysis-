# 代码评审记录

> 跨境电商评论情感挖掘与选品决策支持系统 — 昌平champion盛世  
> 评审周期：2026-07-06 | 评审轮次：第1轮（深度扫描） | 评审负责人：梁思怡

---

## 一、评审概览

| 项目 | 数量 |
|------|:--:|
| 评审文件数 | 8 |
| 发现问题总数 | 36 |
| 🔴 严重 | 7 |
| 🟡 一般 | 21 |
| 🟢 建议 | 9 |
| 已修复 | 6 |
| 待修复 | 28 |
| 待讨论 | 2 |

---

## 二、评审结果明细

### 2.1 数据采集层

#### aliexpress_scraper.py — 评审人：黄子涵

| 编号 | 行号 | 严重度 | 问题描述 | 修改建议 | 责任人 | 状态 |
|:--:|------|:--:|------|------|:--:|:--:|
| CR001 | 100,109,179,182,192,199 | 🟡 | 多处 `raise Exception` 泛化异常，调用方无法按异常类型做区分处理 | 定义自定义异常类（`TokenExpiredError`、`ApiResponseError`等），按场景抛出 | 李思霖 | 🔲 |
| CR002 | 39 | 🔴 | `_m_h5_tk` Cookie令牌硬编码在源码中，是认证凭据，泄漏将导致账号风险 | 改为从环境变量或外部配置文件读取，源码中仅保留占位符 | 李思霖 | 🔲 |
| CR003 | 65 | 🟢 | `CACHE_TTL = 300` 未说明单位（秒？毫秒？） | 改为 `CACHE_TTL_SECONDS = 300` 并加注释 | 李思霖 | 🔲 |
| CR004 | 46 | 🟡 | 代理地址 `127.0.0.1:7897` 硬编码 | 改为从配置文件读取 | 李思霖 | 🔲 |
| CR005 | 293~296 | 🟡 | `except Exception` 捕获过宽 + 无限重试——签名算法失效等不可恢复错误也会永远循环 | 增加最大重试次数上限（3次），不可恢复异常直接终止 | 李思霖 | 🔲 |
| CR006 | 128~133 | 🟡 | `_get_seller_seq` 正则匹配失败时返回硬编码默认值 `2678280160`，对其他商品可能无效 | 默认值改为空字符串，调用方做防御判断 | 李思霖 | 🔲 |
| CR007 | 126 | 🟢 | User-Agent 固定为单一值，易被反爬识别 | 维护 UA 池并随机轮换 | 李思霖 | 🔲 |
| CR008 | 291 | 🟢 | `time.sleep(1.5)` 固定延时，无抖动，请求模式可被识别 | 使用 `random.uniform(1.0, 3.0)` 随机化延时 | 李思霖 | 🔲 |
| CR009 | 246 | 🟢 | `scrape_product` 接收 `csv.DictWriter` 参数，紧耦合——如需输出JSON/数据库无法复用 | 改为返回生成器或列表，由 `main()` 负责写入 | 李思霖 | 🔲 |

---

### 2.2 数据分析层

#### sentiment_analysis.py — 评审人：胡子琦

| 编号 | 行号 | 严重度 | 问题描述 | 修改建议 | 责任人 | 状态 |
|:--:|------|:--:|------|------|:--:|:--:|
| CR009 | 22~34 | 🔴 | UDF内每处理一条记录都 `new SentimentIntensityAnalyzer()`，16,972条=16,972次实例化，**严重拖慢性能** | 实例化为模块级单例，UDF 内仅调用 `.polarity_scores()` | 黄子涵 | 🔲 |
| CR010 | 72 | 🟡 | Python f-string 拼接 `max_cnt` 到SQL，虽然当前来源安全，但一旦数据来源改变即引入 SQL 注入风险 | 改为参数化写法或 DataFrame API | 黄子涵 | 🔲 |
| CR012 | 53~54 | 🟡 | `DROP TABLE IF EXISTS` 后紧跟 `CREATE TABLE AS`——`.write.mode("overwrite").saveAsTable()` 一条即可完成原子覆盖 | 统一为 DataFrame API 方式，避免 DDL 与 DataFrame 混用 | 黄子涵 | 🔲 |
| CR013 | 107 | 🟡 | `spark.stop()` 无 `try/finally` 保护，前面任何步骤抛异常都不会关闭 SparkSession | 用 `try/finally` 包裹主逻辑 | 黄子涵 | 🔲 |
| CR014 | 1~2 | 🟡 | 缺少文件头（文件名/功能/作者/日期）注释 | 按编码规范第 4.2 节补齐文件头 | 黄子涵 | 🔲 |
| CR015 | 4~5 | 🟢 | 导入风格与 `build_deep_ads.py` 不一致——本文件逐个导入函数名，另一文件用 `import functions as F` | 协商统一为 `F.` 前缀方式 | 黄子涵 | 🔲 |

#### build_deep_ads.py — 评审人：胡子琦

| 编号 | 行号 | 严重度 | 问题描述 | 修改建议 | 责任人 | 状态 |
|:--:|------|:--:|------|------|:--:|:--:|
| CR016 | 20~21 | 🟡 | `to_mysql` 写入后立即 `.count()` 打印行数，触发完整重计算 | 写入前 `.cache().count()` 并复用缓存后的 DataFrame | 黄子涵 | 🔲 |
| CR018 | 40~44 | 🟡 | 情感标记规则硬编码英文特征值（`Fast/Good/Great/Poor/Difficult/Fits ok`），新特征值全部归为 neutral | 抽取为可配置字典，增加未匹配特征值日志记录 | 黄子涵 | 🔲 |
| CR019 | 46,67,76,91,109,127 | 🟡 | 6处 `DROP TABLE IF EXISTS` 冗余——之后紧跟 `mode("overwrite")` 已经是覆盖写 | 移除所有多余的 DROP TABLE 语句 | 黄子涵 | 🔲 |
| CR020 | 76~81 | 🟡 | 变量名 `top5_countries` 但 SQL 中 `LIMIT 10`，变量名误导 | 改名 `top_countries` 或 SQL 改为 `LIMIT 5` | 黄子涵 | 🔲 |
| CR021 | 33~36 | 🟡 | `groupBy` 中使用 `.alias()` 写别名，在某些 Spark 版本中行为不确定 | 分组后用 `.withColumnRenamed()` 或在 agg 之后再 alias | 黄子涵 | 🔲 |
| CR022 | 87 | 🟡 | 分国家SKU偏好：取 TOP10 国家 join 后未重新排序，可能混入非TOP10数据 | 最终输出前加 `.orderBy(desc("review_count"))` | 黄子涵 | 🔲 |
| CR023 | 100~107 | 🟢 | `trend` DataFrame 使用字符串列名而非 `F.col()`，与文件其他部分风格不一致 | 统一使用 `F.col()` | 黄子涵 | 🔲 |
| CR024 | 135 | 🟡 | `spark.stop()` 无 `try/finally` 保护（与 CR014 同一问题） | 统一修复 | 黄子涵 | 🔲 |
| CR025 | 全局 | 🟢 | 脚本缺少 `if __name__ == "__main__":` 入口保护，被 import 时会直接执行 | 将顶层执行逻辑包裹在 `main()` 函数中 | 黄子涵 | 🔲 |

---

### 2.3 数据工程层（Scala）

#### rebuild_all.scala — 评审人：李思霖

| 编号 | 行号 | 严重度 | 问题描述 | 修改建议 | 责任人 | 状态 |
|:--:|------|:--:|------|------|:--:|:--:|
| CR025 | 4~25 | 🟡 | 全部 SQL 写成单行，部分超过 150 字符，几乎不可读 | 用 Scala 多行字符串 `"""..."""` 格式化，每行≤100字符 | 李思霖 | 🔲 |
| CR028 | 1~43 | 🟡 | 全文件**零注释**——无功能说明、无建表用途描述 | 每个 `CREATE TABLE` 前加一行中文注释说明表用途 | 李思霖 | 🔲 |
| CR029 | 1~43 | 🟡 | 全文件**零错误处理**——任何一条 SQL 失败都中断且无上下文日志 | 每条 SQL 用 `try/catch` 包裹，失败时打印表名和SQL | 李思霖 | 🔲 |
| CR030 | 1~2 | 🟢 | 仅 `import SaveMode`，依赖 spark-shell 隐式注入，脱离 REPL 环境无法编译 | 加注释说明运行方式，或声明 spark 变量类型 | 李思霖 | 🔲 |
| CR031 | 30~41 | 🟢 | 6次 `.jdbc()` 调用逐个写死，未用循环复用 | 抽取为函数或使用 `Seq + foreach`，与 `export_mysql.scala` 风格统一 | 李思霖 | 🔲 |

#### export_mysql.scala — 评审人：李思霖

| 编号 | 行号 | 严重度 | 问题描述 | 修改建议 | 责任人 | 状态 |
|:--:|------|:--:|------|------|:--:|:--:|
| CR029 | 7 | 🟡 | 13 个表名挤在单行超过 180 字符，新增/修改表名时极易遗漏 | 改为多行列表格式，每行一个表名 | 李思霖 | 🔲 |
| CR034 | 14 | 🔴 | `System.exit(0)` 暴力终止 JVM——Spark 可能还在异步写入，强制退出可能导致数据不完整 | 改为 `.awaitTermination()` 或确认所有 write 完成后正常退出 | 李思霖 | 🔲 |
| CR035 | 9~11 | 🟡 | 单个表写入失败只打印 "OK" 无异常捕获——某张表失败后后续表继续执行，用户不知道中间有失败 | 每表单独 `try/catch`，收集失败表列表最后统一报告 | 李思霖 | 🔲 |

---

### 2.4 后端服务（Java）

#### ApiController.java — 评审人：曹煜权

| 编号 | 行号 | 严重度 | 问题描述 | 修改建议 | 责任人 | 状态 |
|:--:|------|:--:|------|------|:--:|:--:|
| CR036 | 110~149 | 🔴 | `decision()` 方法一次调用执行 **7 次独立 SQL 查询**——每切换一次商品/国家就 7 次数据库 Round-Trip | 合并为一个存储过程，或用一次多结果集查询完成；至少加上缓存 | 曹煜权 | 🔲 |
| CR037 | 17~18 | 🟡 | SQL 别名在**同一方法内**混用 camelCase（`totalReviews`、`avgStar`）和 snake_case（`review_count`、`avg_star`），前端接收到的 JSON key 风格不统一 | 统一改为 snake_case，与 MySQL 列名一致 | 曹煜权 | 🔲 |
| CR038 | 17/22/27/... | 🟡 | 核心业务 SQL 全部硬编码在 Controller 层——Controller 应仅做路由，SQL 应下放到 Service/Repository 层 | 拆分三层：Controller → Service → Repository | 曹煜权 | 🔲 |
| CR039 | 114~116 | 🟡 | `.forEach` 遍历全量 scorecard 结果匹配 productId——O(n) 且无早停 | 改为 `WHERE product_id=?` 参数化查询直接返回目标行 | 曹煜权 | 🔲 |
| CR040 | 22/27/32/37/42/47/52/57 | 🟡 | 全部列表接口无条件 `LIMIT`，数据积累后可能返回数万行导致 OOM 和响应超时 | 所有列表接口增加默认 `LIMIT` 和分页参数 | 曹煜权 | 🔲 |
| CR041 | 1~150 | 🟡 | 类及所有方法均无 Javadoc、无 Swagger 注解——API 文档只能靠读代码 | 补充 OpenAPI (Swagger) 注解和 Javadoc | 曹煜权 | 🔲 |
| CR042 | 74/84/93/102 | 🟡 | `@PathVariable` 参数未做校验——空字符串或特殊字符可能导致 SQL 异常 | 增加 `@NotBlank` / `@Pattern` 等注解校验 | 曹煜权 | 🔲 |
| CR043 | 1~150 | 🟢 | 无任何缓存机制——大屏每次切换 tab 都重新查询全部数据 | 不常变数据（国家列表、基础统计）加 `@Cacheable` 缓存 | 曹煜权 | 🔲 |
| CR044 | 1~150 | 🟡 | 无全局异常处理器——数据库异常时 Spring 返回 HTML 错误页或 stack trace | 增加 `@ControllerAdvice`，统一返回 JSON 错误格式 | 曹煜权 | 🔲 |
| CR045 | 全局 | 🟢 | 方法名缩写不统一（`overview`、`sku` 短缩写 vs `imageFollowup`、`sentimentProduct` 完整名） | 统一为完整 camelCase，如 `getSkuAnalysis()` | 曹煜权 | 🔲 |

#### CorsConfig.java — 评审人：曹煜权

| 编号 | 行号 | 严重度 | 问题描述 | 修改建议 | 责任人 | 状态 |
|:--:|------|:--:|------|------|:--:|:--:|
| CR046 | 14 | 🔴 | `addAllowedOriginPattern("*")` 允许任意来源跨域——攻击者可在任意网站嵌入请求 | 改为白名单模式，仅允许前端部署域名 | 曹煜权 | 🔴 待讨论 |
| CR047 | 14+17 | 🔴 | `allowCredentials(true)` + `origin("*")` 组合——**W3C CORS 规范明确禁止**，主流浏览器直接拦截，CORS 配置实际不生效 | 如前端无 Cookie/Token，关闭 `allowCredentials`；否则 origin 必须指定具体域名 | 曹煜权 | 🔴 待讨论 |
| CR048 | 15~16 | 🟡 | `addAllowedMethod("*")` + `addAllowedHeader("*")` 开放全部方法和头，暴露过多攻击面 | 限制为实际需要：Method 仅 GET，Header 仅 Content-Type | 曹煜权 | 🔲 |
| CR049 | 1~22 | 🟢 | 全类零注释——未说明哪种环境用什么策略、为什么允许 Credentials | 添加 Javadoc 说明 CORS 策略意图和使用范围 | 曹煜权 | 🔲 |

---

### 2.5 前端可视化（Vue）

#### App.vue — 评审人：胡子琦

| 编号 | 行号 | 严重度 | 问题描述 | 修改建议 | 责任人 | 状态 |
|:--:|------|:--:|------|------|:--:|:--:|
| CR050 | 6 | 🔴 | API 地址硬编码——IP 变动前端直接不可用 | ✅ 已改用环境变量 `VITE_API_BASE_URL` | 曹煜权 | ✅ |
| CR051 | 182+188 | 🔴 | **ch5 图表 DOM id 重复出现两次** | ✅ 删除重复卡片 + 抽取 `renderFeatureChart()` 公共函数 | 曹煜权 | ✅ |
| CR052 | 46 | 🟡 | `setTimeout(150)` 拍脑袋延时渲染图表 | ✅ 3处全部改为 `nextTick()` | 曹煜权 | ✅ |
| CR053 | 21~29 | 🟡 | 大量硬编码字典全塞在组件顶部 | 抽取到独立的 `src/data/translations.js` | 曹煜权 | 🔲 |
| CR054 | 53~89 | 🟡 | `loadAll()` 函数体过长（37行） | 拆分为 `loadDecision()`/`loadCharts()`/`loadCountryInsight()` | 曹煜权 | 🔲 |
| CR055 | 96~113 | 🟡 | ECharts option 对象直接内嵌在 `renderCharts()` 内 | 每个图表抽取为 `getChartXOption()` 工厂函数 | 曹煜权 | 🔲 |
| CR056 | 109~136 | 🟡 | feature 好评/差评过滤逻辑5+次重复 | ✅ 已抽取为 `isPositiveFeature()` / `isNegativeFeature()` | 曹煜权 | ✅ |
| CR057 | 64/68~70/84 | 🟡 | axios 请求无用户端错误提示 | ✅ 已加 `apiGet()` 统一错误处理 + `console.error` 日志 | 曹煜权 | ✅ |
| CR058 | 全局 | 🟡 | 变量缩写严重（`td`/`cc`/`cn`/`cf`/`ct`等） | ✅ 13个变量已全部重命名为有意义的英文名 | 曹煜权 | ✅ |
| CR059 | ~70 | 🟡 | `countryInsight.value` 内 Map key 混用 camelCase（`reviewCount`）和 snake_case（`featData`），与后端 CR038 问题联动 | 后端统一 snake_case 后，前端同步 | 曹煜权 | 🔲 |
| CR060 | 73+85 | 🟢 | 无 `console.error` 日志，前端报错时排查困难 | catch 块中增加 `console.error(error.message)` | 曹煜权 | 🔲 |

---

## 三、跨文件通用问题（合并修复）

以下问题同时出现在多个文件中，应统一处理，避免重复劳动：

| 编号 | 问题 | 影响文件 | 统一方案 | 责任人 |
|:--:|------|------|------|:--:|
| X01 | `spark.stop()` 无 `try/finally` 保护 | `sentiment_analysis.py:107`、`build_deep_ads.py:135`（共2处） | 统一用 `try/finally` 包裹主逻辑 | 黄子涵 |
| X02 | MySQL 表导出逻辑重复实现 | `rebuild_all.scala`、`export_mysql.scala` 各自实现几乎相同的 jdbc 写入循环 | 合并为一个公共导出模块，两个脚本调用它 | 李思霖 |

---

## 四、评审总结

### 4.1 评审结论

**评审结果：⚠️ 条件通过（41 个问题，0 个阻断性缺陷）**

核心功能代码逻辑正确，无导致系统不可用的阻断性 Bug。问题集中在：

| 类别 | 数量 | 典型案例 |
|------|:--:|------|
| 凭据/配置硬编码 | 🔴 2 | Cookie令牌1处、API地址1处 |
| 性能隐患 | 🔴 3 | VADER重复实例化、7次SQL串行、无缓存 |
| 编码规范不足 | 🟡 12 | Scala零注释、SQL单行超长、变量缩写、别名混用 |
| 错误处理缺失 | 🟡 8 | 无try/finally、无异常处理器、无用户提示 |
| CORS 配置风险 | 🔴 2 | 通配符origin + allowCredentials组合 |
| 代码结构 | 🟡 5 | Controller过重、函数过长、重复逻辑 |
| 其他建议 | 🟢 5 | UA池、延时抖动、Javadoc、Swagger |

### 4.2 修复优先级

| 优先级 | 编号 | 说明 | 影响 |
|:--:|------|------|------|
| **v3.0 W1** | CR010、CR035、CR051、CR052 | System.exit+API硬编码+DOM id重复 | 影响运行稳定性和安全性 |
| **v3.0 W1** | CR012、CR013、CR014、CR020、CR025、CR029、CR030、CR034、CR038、CR058 | 代码质量基础修复 | 影响可维护性和演示体验 |
| **v3.0 W2** | CR037、CR039~CR044、CR053~CR056、CR059~CR060 | 架构重构和交互优化 | 影响答辩大屏体验 |
| **v3.0 W3** | CR047~CR049 | CORS配置：答辩时口头说明，无需改代码 | 安全答辩加分项 |
| **可选** | CR002~CR009、CR015、CR016、CR018、CR019、CR021~CR023、CR026、CR028、CR031、CR032、CR036、CR046 | 锦上添花，时间充裕则做 | 代码质量长期收益 |

### 4.3 评审参与

| 角色 | 姓名 | 评审范围 |
|------|------|------|
| 评审负责人 | 梁思怡 | 全项目统筹评审 |
| 评审员 | 黄子涵 | Python 数据采集+分析脚本（CR001~CR010） |
| 评审员 | 胡子琦 | Python 分析脚本 + 前端代码（CR010~CR025 + CR051~CR061） |
| 评审员 | 李思霖 | Scala 大数据工程脚本（CR027~CR036） |
| 评审员 | 曹煜权 | Java 后端 + Vue 前端（CR037~CR061） |

### 4.4 第二轮评审计划

| 时间 | 范围 | 标准 |
|------|------|------|
| v3.0 第1周末 | W1 修复项（13项）全部复验 | 每项必须关闭或标记为"延期" |
| v3.0 第2周末 | W2 修复项（15项）全部复验 | 同上 |
| v3.0 第3周末 | v3.0 终审：所有未关闭项 | 答辩前最终确认 |

---

## 五、修复跟踪

| 日期 | 编号 | 操作 | 操作人 |
|------|:--:|------|:--:|
| 07-06 | CR050 | API地址改为 Vite 环境变量 `VITE_API_BASE_URL` | 曹煜权 |
| 07-06 | CR051 | 删除重复 ch5 卡片，替换为数据总览说明 | 曹煜权 |
| 07-06 | CR056 | 5处重复过滤逻辑提取为 `isPositiveFeature` / `isNegativeFeature` | 曹煜权 |
| 07-06 | CR057 | axios 统一 `apiGet()` 错误处理，catch 加 `console.error` | 曹煜权 |
| 07-06 | — | 新增：ABSA图无数据占位 + `isPositiveFeature/isNegativeFeature` score trim化 | 曹煜权 |
| 07-07 | CR052 | 3处 `setTimeout(150)` → `nextTick()` | 曹煜权 |
| 07-07 | CR058 | 13个变量重命名（`td`→`allData`、`cc`→`createChart`等） | 曹煜权 |
| 07-07 | — | 新增数据质量报告Tab（替代历史记录） | 曹煜权 |
| 07-07 | — | 新增5品类关键词特征标注（`tag_features.py`） | 梁思怡 |
| 07-08 | — | 新增 Pandas/Numpy EDA + LDA 主题模型 + MR vs Spark 对比 | 梁思怡 |
| 07-08 | — | 新增项目总览文档 + API清单 + 3张可视化图表 | 梁思怡 |
