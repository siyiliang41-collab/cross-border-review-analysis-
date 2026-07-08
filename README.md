# 跨境电商评论情感挖掘与选品决策支持系统

> 昌平champion盛世 | v3.0 | 2026-07

## 项目简介

基于速卖通5品类19,248条用户评论的全链路情感挖掘与选品决策系统。

- **数据源：** AliExpress mtop API — 蓝牙耳机/手机壳/LED小夜灯/连衣裙/油壶
- **技术栈：** Python爬虫 → Hive四层数仓 → Spark → MySQL → SpringBoot → Vue3+ECharts
- **分析能力：** VADER情感打分 + ABSA产品特征抽取 + 国家×品类适配度矩阵 + 选品评分卡

## 目录结构

```
├── scraper/       ← 数据采集（速卖通评论爬虫 v3）
├── data/          ← 原始数据（CSV）
├── spark/         ← 大数据分析（数仓重建/情感分析/深度ADS/特征标注）
├── backend/       ← 后端服务（SpringBoot 3.2 + MyBatis）
├── frontend/      ← 前端大屏（Vue3 + Vite + ECharts）
└── docs/          ← 项目文档（编码规范/评审记录/里程碑/操作手册）
```

## 快速开始

详见 [docs/operations-guide.md](docs/operations-guide.md)

## 团队

- 梁思怡 — 项目经理 + 系统设计
- 李思霖 — 大数据开发 + 数据架构
- 黄子涵 — 数据分析与算法
- 曹煜权 — 后端 + 前端
- 胡子琦 — 测试 + 文档
