# 跨境电商评论情感挖掘与选品决策支持系统

> 昌平champion盛世 | v5.0 | 2026-07-09

## 项目简介

基于速卖通5品类评论的全链路情感挖掘与选品决策系统。

| 数据指标 | 数值 |
|---|---|
| CSV 原始数据 | 19,271 条 |
| DWD 清洗后 | 19,248 条（过滤率 0.12%） |
| 覆盖国家 | 102 个（≥3条评论） |
| 时间跨度 | 2025-07 ~ 2026-07（13 个月） |
| 分析品类 | 蓝牙耳机/手机壳/LED小夜灯/连衣裙/油壶 |

- **技术栈：** Python爬虫 → Hive四层数仓 → Spark → MySQL → SpringBoot → Vue3+ECharts
- **ML 算法：** LDA 主题聚类 + KMeans 国家分群 + 线性回归预测 + VADER一致性校验
- **前端：** 5Tab（概览/产品洞察/市场洞察/数据质量/数据管理），Element Plus CRUD + JWT 登录认证
- **认证：** 管理员可增删改，普通用户仅查看
- **部署：** 局域网 `192.168.229.101:8080`（前端内嵌 JAR）+ ngrok 公网穿透

## 目录结构

```
├── scraper/       ← 数据采集（速卖通评论爬虫 v3）
├── data/          ← 原始数据（CSV）
├── spark/         ← 大数据分析（数仓重建/情感分析/LDA/KMeans/时序预测/Pandas EDA）
├── backend/       ← 后端服务（SpringBoot 3.2 + 22个 REST API + JWT认证）
├── frontend/      ← 前端大屏（Vue3+Vite+ECharts+ElementPlus，JWT登录+5Tab）
├── docs/          ← 项目文档（9个）
└── charts/        ← 分析图表产物（5张PNG）
```

## 访问地址

| 场景 | 地址 |
|------|------|
| **局域网**（答辩主力） | `http://192.168.229.101:8080` |
| 公网穿透（备用） | `https://squint-owl-worshiper.ngrok-free.dev` |

## 快速开始

详见 [docs/operations-guide.md](docs/operations-guide.md)

## 团队

- 梁思怡 — 项目经理 + 系统设计
- 李思霖 — 大数据开发 + 数据架构
- 黄子涵 — 数据分析与算法
- 曹煜权 — 后端 + 前端
- 胡子琦 — 测试 + 文档
