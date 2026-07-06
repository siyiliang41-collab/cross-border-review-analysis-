# 编码规范

> 跨境电商评论情感挖掘与选品决策支持系统 — 团队统一编码标准  
> 版本：v1.0 | 制定：昌平champion盛世 | 最后更新：2026-07-06

---

## 1. 总则

### 1.1 适用范围

本文档适用于本项目所有代码文件，包括但不限于：

| 语言 | 涉及文件 |
|------|---------|
| Python | 爬虫脚本、分析脚本、CSV处理 |
| Scala | Spark SQL 数仓构建、数据导出 |
| Java | SpringBoot 后端 RESTful API |
| Vue/JavaScript | 前端大屏可视化，ECharts 图表 |

### 1.2 核心原则

1. **一致性优先** — 同一语言内部风格统一，不混用多种命名惯例
2. **可读性优先** — 命名见名知义，函数单一职责，注释解释"为什么"而非"是什么"
3. **中文注释** — 所有注释、文档、提交说明均使用中文

### 1.3 文件编码

- 所有源码文件统一使用 **UTF-8** 编码
- 禁止使用 GBK、GB2312、Latin-1 等其他编码
- IDE 设置：`files.encoding: utf8`，`files.autoGuessEncoding: false`

---

## 2. 命名规范

### 2.1 Python

| 元素 | 风格 | 示例 |
|------|------|------|
| 文件名 | `snake_case` | `aliexpress_scraper.py`、`sentiment_analysis.py` |
| 变量 | `snake_case` | `buyer_country`、`review_count`、`star_rating` |
| 函数 | `snake_case` | `flatten_csv()`、`compute_sentiment()`、`build_ads_tables()` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_PAGES = 200`、`APP_KEY = "12574478"` |
| 类名 | `PascalCase` | 本项目暂未使用类（均为脚本式），如需使用则遵守此规范 |
| 私有函数 | `_leading_underscore` | `_generate_sign()`、`_parse_jsonp_response()` |

```python
# ✅ 正确示例
MAX_RETRY = 3
session_timeout = 30

def fetch_reviews(product_id: str, page: int) -> list:
    """根据商品ID和页码获取评论列表"""
    reviews = []
    for attempt in range(MAX_RETRY):
        data = _request_api(product_id, page)
        if data:
            reviews.extend(data)
    return reviews

def _generate_sign(token: str, timestamp: str, app_key: str, data: str) -> str:
    """生成 mtop 接口 MD5 签名（内部函数）"""
    ...

# ❌ 错误示例
MaxRetry = 3                    # 常量应用全大写
sessiontimeout = 30             # 单词间应用下划线分隔
def FetchReviews(pid, p): ...   # 函数应用 snake_case，参数应见名知义
```

### 2.2 Scala

| 元素 | 风格 | 示例 |
|------|------|------|
| 文件名 | `snake_case` | `rebuild_all.scala`、`export_mysql.scala` |
| 变量/val | `camelCase` | `dwdClean`、`productStats`、`sentimentDf` |
| 函数/def | `camelCase` | `rebuildDwd()`、`computeAds()` |
| 对象/单例 | `PascalCase` | `RebuildAll`、`ExportMysql` |

```scala
// ✅ 正确示例
val productStats = spark.sql("""
    SELECT product_id, COUNT(*) AS cnt, AVG(star_rating) AS avg_star
    FROM dwd_reviews GROUP BY product_id
""")

// ❌ 错误示例
val product_stats = ...   // Scala 中变量使用 camelCase，不用 snake_case
```

### 2.3 Java

| 元素 | 风格 | 示例 |
|------|------|------|
| 类名 | `PascalCase` | `ApiController`、`CorsConfig`、`BiptApplication` |
| 方法 | `camelCase` | `getOverview()`、`queryByProductId()` |
| 变量 | `camelCase` | `jdbcTemplate`、`productList` |
| 常量 | `UPPER_SNAKE_CASE` | `API_PREFIX`、`DEFAULT_PAGE_SIZE` |
| 包名 | 小写，无下划线 | `com.bipt.controller`、`com.bipt.config` |

```java
// ✅ 正确示例
@RestController
public class ApiController {

    @Autowired
    private JdbcTemplate jdbc;

    @GetMapping("/api/products/rating")
    public List<Map<String, Object>> getProductRatings() {
        return jdbc.queryForList(
            "SELECT product_id, avg_star FROM ads_product_rating ORDER BY avg_star DESC"
        );
    }
}

// ❌ 错误示例
public class api_controller { ... }        // 类名应用 PascalCase
public List get_product_ratings() { ... }  // 方法应用 camelCase
```

### 2.4 Vue / JavaScript

| 元素 | 风格 | 示例 |
|------|------|------|
| 组件文件 | `PascalCase` | `App.vue`、`CountryInsight.vue` |
| 配置/工具文件 | `camelCase` 或 `kebab-case` | `main.js`、`vite.config.js` |
| 变量 | `camelCase` | `selectedProduct`、`countryMap`、`chartOptions` |
| 函数 | `camelCase` | `fetchData()`、`renderChart()`、`onProductChange()` |
| 常量 | `UPPER_SNAKE_CASE` | `API_BASE_URL`、`PRODUCT_LIST`、`COUNTRY_NAMES` |
| CSS 类名 | `kebab-case` | `.card-title`、`.chart-container`、`.tab-panel` |

```javascript
// ✅ 正确示例
const API = "http://192.168.229.101:8080/api"
const PRODUCT_NAMES = { "3256808363596774": "蓝牙耳机", ... }

async function fetchProductStats(productId) {
    const response = await axios.get(`${API}/products/rating`)
    return response.data
}

// ❌ 错误示例
const api_base_url = "..."               // 常量应用全大写
function fetch_product_stats(pid) { ... } // 函数应用 camelCase
```

---

## 3. 格式规范

### 3.1 缩进

| 语言 | 缩进方式 | 宽度 |
|------|----------|:--:|
| Python | 空格 | 4 |
| Scala | 空格 | 2 |
| Java | 空格 | 4 |
| JavaScript/Vue | 空格 | 2 |
| XML/POM | 空格 | 4 |

### 3.2 行宽

- 建议不超过 **120** 字符
- SQL 字符串拼接不受此限制（以可读性优先）

### 3.3 空行

- 函数/方法之间保留一个空行
- 逻辑段落之间保留一个空行
- import 语句与类/函数定义之间保留一个空行

---

## 4. 注释规范

### 4.1 语言要求

**所有注释必须使用中文。** 这是项目强制性要求，不接受英文注释。

### 4.2 文件头注释

每个源文件开头必须有文件头注释：

```python
"""
文件名：aliexpress_scraper.py
功能：速卖通 mtop API 评论爬虫，支持 MD5 签名生成与断点续爬
作者：李思霖
创建日期：2026-06-22
修改记录：
  - 2026-06-22：初始版本，实现基础爬虫逻辑
  - 2026-06-23：修复 Cookie 过期自动重试机制
"""
```

### 4.3 函数注释

```python
def generate_sign(token: str, timestamp: str, app_key: str, data: str) -> str:
    """
    生成 mtop 接口 MD5 签名
    
    参数:
        token: 从 Cookie _m_h5_tk 中提取的 token 值
        timestamp: 毫秒级 Unix 时间戳
        app_key: 应用密钥（web端固定为 12574478）
        data: JSON 格式的请求参数
    
    返回:
        32位十六进制 MD5 签名字符串
    
    签名公式: MD5(token & timestamp & appKey & data_json)
    """
    ...
```

### 4.4 行内注释

- 解释**为什么**这样做，而非代码在做什么
- 标注 TODO/FIXME/HACK 时需要注明负责人和日期

```python
# TODO(李思霖 2026-07-10): 放开200页限制，支持全量数据采集
# FIXME: 部分评论的 eval_date 字段为空，需排查上游 CSV 列对齐问题
```

---

## 5. SQL 编写规范

### 5.1 关键字大小写

- SQL 关键字统一使用**大写**
- 表名、列名使用**小写 + 下划线**

```sql
-- ✅ 正确
SELECT product_id, buyer_country, COUNT(*) AS review_count
FROM ads_country_product_matrix
WHERE product_id = ?
ORDER BY review_count DESC
LIMIT 10

-- ❌ 错误
select product_id, buyer_country, count(*) as review_count
from ads_country_product_matrix
where product_id = ?
order by review_count desc
limit 10
```

### 5.2 别名

- 聚合函数结果必须使用 `AS` 别名
- 别名使用 snake_case

---

## 6. Git 提交规范

### 6.1 Commit Message 格式

```
<type>: <简短中文描述>

- <详细变更要点1>
- <详细变更要点2>
```

### 6.2 Type 类型

| 类型 | 含义 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 新增选品评分卡 ADS 表` |
| `fix` | Bug 修复 | `fix: 修复 eval_date 全部为 NULL 的问题` |
| `refactor` | 重构（不改变功能） | `refactor: 后端工程标准化，Maven 目录结构` |
| `chore` | 工程配置 | `chore: 初始化 .gitignore 和编码设置` |
| `docs` | 文档 | `docs: 新增编码规范文档` |
| `perf` | 性能优化 | `perf: Spark 增加 broadcast hint 减少 shuffle` |

### 6.3 提交粒度

- **一次提交只做一件事** — 不混搭（如修复Bug和新功能分开提交）
- 单个提交的变更行数建议不超过 **500 行**
- 提交前确认 `.gitignore` 有效，不会误交依赖包或临时文件

---

## 7. 项目目录结构

```
bipt-project/
├── .gitignore                  # Git 忽略规则
├── docs/                       # 项目文档
│   └── coding-standards.md     # 编码规范（本文件）
├── aliexpress_scraper.py       # 数据采集：爬虫脚本
├── aliexpress_reviews.csv      # 原始数据：16,989 条评论
├── sentiment_analysis.py       # 情感分析：VADER 打分脚本
├── build_deep_ads.py           # 深度分析：ADS 表构建
├── rebuild_all.scala           # 数仓重建：ODS→DWD→DWS→ADS
├── export_mysql.scala          # 数据导出：Spark JDBC → MySQL
├── bipt-api/                   # 后端：SpringBoot + Maven
│   ├── pom.xml
│   └── src/main/
│       ├── java/com/bipt/
│       │   ├── BiptApplication.java
│       │   ├── controller/ApiController.java
│       │   └── config/CorsConfig.java
│       └── resources/
│           └── application.properties
└── bipt-dashboard/             # 前端：Vue3 + Vite + ECharts
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.js
        ├── App.vue
        └── style.css
```

---

## 8. 检查清单

提交代码前逐项确认：

- [ ] 文件名符合所属语言的命名规范
- [ ] 变量/函数/类名符合规范，见名知义
- [ ] 所有注释使用中文
- [ ] 文件头注释完整（文件名+功能+作者+日期）
- [ ] 缩进统一（Python 4空格 / Java 4空格 / Vue 2空格）
- [ ] 无硬编码密码或密钥（应放入配置文件或环境变量）
- [ ] 无调试用 print/console.log
- [ ] `.gitignore` 生效，未提交 node_modules / __pycache__ / .claude
- [ ] Commit message 格式正确，一件提交只做一件事
