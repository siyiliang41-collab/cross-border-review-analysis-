# -*- coding: utf-8 -*-
"""
文件名：kmeans_country_cluster.py
功能：KMeans 国家分群 — 135个国家按消费行为聚成3~4类市场画像
      补全课程核心阶段要求的 ML 分类算法
作者：梁思怡
创建日期：2026-07-09
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 1. 加载数据 & 构建国家特征矩阵
# ============================================================
print("=" * 60)
print("  KMeans 国家分群 — 跨境电商消费市场聚类")
print("=" * 60)

CSV_PATH = "../data/aliexpress_reviews.csv"
df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
df['productId'] = df['productId'].astype(str).str.replace('﻿', '').str.strip()
df['buyerCountry'] = df['buyerCountry'].astype(str).str.strip()

# 按国家聚合特征
country_features = df.groupby('buyerCountry').agg(
    评论数=('evaluationId', 'count'),
    平均星评=('starRating', 'mean'),
    星评标准差=('starRating', 'std'),
    带图率=('hasImage', 'mean'),
    追评率=('hasFollowUp', 'mean'),
    品类数=('productId', 'nunique'),
).reset_index()

# 去掉标准差为 NaN 的国家（只有1条评论的）
country_features = country_features.dropna(subset=['星评标准差'])
country_features = country_features[country_features['评论数'] >= 3]  # 至少3条评论才有统计意义

print(f"\n[1/5] 数据结构构建完成")
print(f"   有效国家数: {len(country_features)}")
print(f"   特征维度: 评论数/平均星评/星评标准差/带图率/追评率/品类数")

# ============================================================
# 2. 标准化 + KMeans 聚类
# ============================================================
print(f"\n[2/5] KMeans 聚类...")

feature_cols = ['评论数', '平均星评', '星评标准差', '带图率', '追评率', '品类数']
X = country_features[feature_cols].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 用肘部法则确定最佳 K（实际选了4）
inertias = []
for k in range(2, 7):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_scaled)
    inertias.append(km.inertia_)

# K=4 聚类
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
country_features['cluster'] = kmeans.fit_predict(X_scaled)

# ============================================================
# 3. 各聚类画像分析
# ============================================================
print(f"\n[3/5] 聚类画像分析...")

cluster_profiles = country_features.groupby('cluster').agg(
    国家数=('buyerCountry', 'count'),
    平均评论数=('评论数', 'mean'),
    平均星评=('平均星评', 'mean'),
    平均标准差=('星评标准差', 'mean'),
    平均带图率=('带图率', 'mean'),
    平均品类覆盖=('品类数', 'mean'),
).round(2)

print(f"\n  聚类中心（标准化后）:")
for i in range(4):
    center = kmeans.cluster_centers_[i]
    print(f"  聚类{i}: 评论规模={center[0]:.2f}, 星评={center[1]:.2f}, 波动={center[2]:.2f}, 带图={center[3]:.2f}")

print(f"\n  各聚类统计:")
print(cluster_profiles.to_string())

# 自动标注聚类含义
cluster_labels = {}
for cid in range(4):
    row = cluster_profiles.loc[cid]
    if row['平均星评'] >= cluster_profiles['平均星评'].median() and row['平均评论数'] >= cluster_profiles['平均评论数'].median():
        cluster_labels[cid] = "成熟高价值市场 Star"
    elif row['平均星评'] >= cluster_profiles['平均星评'].median():
        cluster_labels[cid] = "潜力精品市场 Seed"
    elif row['平均评论数'] >= cluster_profiles['平均评论数'].median():
        cluster_labels[cid] = "价格敏感大市场 Box"
    else:
        cluster_labels[cid] = "长尾探索市场 Zoom"

country_features['cluster_label'] = country_features['cluster'].map(cluster_labels)

# 各聚类的代表性国家
print(f"\n  各聚类代表性国家:")
for cid in range(4):
    members = country_features[country_features['cluster'] == cid].nlargest(5, '评论数')
    names = members['buyerCountry'].tolist()
    print(f"  {cluster_labels[cid]} (聚类{cid}): {', '.join(names)}")

# ============================================================
# 4. PCA 降维可视化
# ============================================================
print(f"\n[4/5] PCA 可视化...")

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
country_features['pca_x'] = X_pca[:, 0]
country_features['pca_y'] = X_pca[:, 1]

colors = ['#1565c0', '#2e7d32', '#e65100', '#6a1b9a']
fig, axes = plt.subplots(1, 2, figsize=(16, 6.5))
fig.suptitle("KMeans 国家分群 — 跨境电商消费市场聚类分析", fontsize=16, fontweight='bold')

# 左图：PCA 散点图
for cid in range(4):
    members = country_features[country_features['cluster'] == cid]
    axes[0].scatter(members['pca_x'], members['pca_y'], c=colors[cid], label=cluster_labels[cid],
                    s=members['评论数']/10, alpha=0.7, edgecolors='white', linewidth=0.5)
    # 标注TOP5国家
    for _, row in members.nlargest(5, '评论数').iterrows():
        axes[0].annotate(row['buyerCountry'], (row['pca_x'], row['pca_y']),
                         fontsize=8, ha='center', va='bottom', alpha=0.85)

axes[0].set_title(f"PCA 降维可视化 ({len(country_features)}个国家, 4个聚类)")
axes[0].set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
axes[0].set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
axes[0].legend(fontsize=11, loc='lower right')
axes[0].grid(alpha=0.2)

# 右图：雷达图（聚类轮廓）
axes[1].axis('off')
conclusion_text = ("\n\n  KMeans 市场聚类结论\n\n"
    f"  *  K=4 聚类，覆盖 {len(country_features)} 个国家\n\n"
    "  *  成熟高价值市场（高评分+高活跃）:\n"
    "     推荐重点投入，做品牌化运营\n\n"
    "  *  潜力精品市场（高评分+低活跃）:\n"
    "     评论少但质量高，适合新品试水\n\n"
    "  *  价格敏感大市场（低评分+高活跃）:\n"
    "     价格/物流是主要决策因素\n\n"
    "  *  长尾探索市场（低评分+低活跃）:\n"
    "     暂不推荐重点投入，观察\n\n"
    "  ML 算法: KMeans + PCA 降维\n"
    "  与 LDA 主题模型互补,\n"
    "  一个做文本聚类，一个做用户分群")
axes[1].text(0.05, 0.95, conclusion_text, fontsize=11, transform=axes[1].transAxes,
             verticalalignment='top', linespacing=1.6,
             bbox=dict(boxstyle='round,pad=0.8', facecolor='#f8f9fa', edgecolor='#ccd0d5', linewidth=1.5))

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig("../charts/kmeans_country_clusters.png", dpi=150, bbox_inches='tight')
print("   KMeans 可视化已保存: charts/kmeans_country_clusters.png")

# ============================================================
# 5. 选品建议 — 各聚类 x 各品类星评矩阵
# ============================================================
print(f"\n[5/5] 市场 × 品类推荐矩阵...")

product_names = {
    "3256808363596774": "蓝牙耳机", "3256807406290815": "手机壳",
    "3256807087680846": "LED小夜灯", "3256807145227935": "连衣裙",
    "3256805677493085": "油壶",
}
df['product_name'] = df['productId'].map(product_names)

# 为每个聚类推荐品类
print(f"\n  各市场类型推荐品类:")
for cid in range(4):
    members = country_features[country_features['cluster'] == cid]
    member_countries = members['buyerCountry'].tolist()
    cluster_df = df[df['buyerCountry'].isin(member_countries)]
    prod_rating = cluster_df.groupby('product_name').agg(
        评论数=('starRating', 'count'), 平均星评=('starRating', 'mean')
    ).round(2).sort_values('平均星评', ascending=False)
    print(f"\n  {cluster_labels[cid]}:")
    for pname, row in prod_rating.iterrows():
        print(f"    {pname}: {row['平均星评']} ({row['评论数']:.0f}条)")

print("\n" + "=" * 60)
print("  KMeans 国家分群分析完成")
print("=" * 60)
print(f"""
分析总结:
  1. {len(country_features)} 个国家聚为 4 个消费市场类型
  2. 成功实现 KMeans 无监督分类，与 LDA 主题聚类互补
  3. PCA 降维可解释方差: {pca.explained_variance_ratio_.sum()*100:.1f}%
  4. 为每个市场类型给出了选品推荐建议
  5. ML 算法: LDA(文本聚类) + KMeans(用户分群)，双 ML 支撑
""")
