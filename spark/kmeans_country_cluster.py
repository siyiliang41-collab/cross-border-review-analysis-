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
# 4. PCA 降维可视化（全新设计）
# ============================================================
print(f"\n[4/5] PCA 降维可视化...")

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
country_features['pca_x'] = X_pca[:, 0]
country_features['pca_y'] = X_pca[:, 1]

# === 配色方案（业务语义） ===
PALETTE = {'Star': '#5B3F9E', 'Seed': '#2E9B70', 'Box': '#E6A23C', 'Zoom': '#94A3B8'}
LABEL_FULL = {
    'Star': '成熟高价值市场',
    'Seed': '潜力精品市场',
    'Box':   '价格敏感大市场',
    'Zoom':  '长尾探索市场',
}
LABEL_DESC = {
    'Star': '高评分 + 高活跃 · 推荐重点投入',
    'Seed': '高评分 + 低活跃 · 适合新品试水',
    'Box':   '高活跃 + 评分适中 · 价格/物流是主导',
    'Zoom':  '低活跃 + 低评分 · 暂不推荐重点投入',
}

# 聚类标签统一为中文+代号格式
for cid, orig in cluster_labels.items():
    if 'Star' in orig: cluster_labels[cid] = '成熟高价值 (Star)'
    elif 'Seed' in orig: cluster_labels[cid] = '潜力精品 (Seed)'
    elif 'Box' in orig: cluster_labels[cid] = '价格敏感 (Box)'
    elif 'Zoom' in orig: cluster_labels[cid] = '长尾探索 (Zoom)'

country_features['cluster_label'] = country_features['cluster'].map(cluster_labels)
country_features['color'] = country_features['cluster'].apply(
    lambda c: PALETTE.get(('Star' if 'Star' in cluster_labels[c] else
                            'Seed' if 'Seed' in cluster_labels[c] else
                            'Box' if 'Box' in cluster_labels[c] else 'Zoom'), '#94A3B8'))

# === 大图布局 ===
fig = plt.figure(figsize=(20, 9))
gs = fig.add_gridspec(1, 2, width_ratios=[6, 4], wspace=0.04)

# ── 左：PCA 散点图 ──
ax = fig.add_subplot(gs[0, 0])

# 气泡大小上限（避免 ES 等超大点失控）
size_raw = country_features['评论数'].clip(upper=1000)
sizes = 20 + (size_raw / size_raw.max()) * 280

for cid in range(4):
    members = country_features[country_features['cluster'] == cid]
    tag = ('Star' if 'Star' in cluster_labels[cid] else
           'Seed' if 'Seed' in cluster_labels[cid] else
           'Box' if 'Box' in cluster_labels[cid] else 'Zoom')
    c = PALETTE[tag]
    ax.scatter(members['pca_x'], members['pca_y'], s=sizes[members.index],
               c=c, alpha=0.72, edgecolors='white', linewidth=0.6,
               zorder=3)

# 每聚类 TOP3 标注
for cid in range(4):
    members = country_features[country_features['cluster'] == cid]
    tag = ('Star' if 'Star' in cluster_labels[cid] else
           'Seed' if 'Seed' in cluster_labels[cid] else
           'Box' if 'Box' in cluster_labels[cid] else 'Zoom')
    for _, row in members.nlargest(3, '评论数').iterrows():
        ax.annotate(row['buyerCountry'],
                    (row['pca_x'], row['pca_y']),
                    fontsize=10, fontweight='bold', color='#1E293B',
                    ha='center', va='bottom',
                    xytext=(0, 7), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                              edgecolor='none', alpha=0.82))

# 坐标轴 & 网格轻量化
ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)",
              fontsize=12, color='#64748B', labelpad=10)
ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)",
              fontsize=12, color='#64748B', labelpad=10)
ax.tick_params(labelsize=10, colors='#94A3B8', length=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#E2E8F0')
ax.spines['bottom'].set_color('#E2E8F0')
ax.grid(True, axis='y', color='#F1F5F9', linewidth=0.8)
ax.grid(True, axis='x', color='#F1F5F9', linewidth=0.8)

# 图例 — 图表底部，左对齐，带业务含义
legend_elements = []
legend_order = ['Star', 'Box', 'Seed', 'Zoom']
for tag in legend_order:
    legend_elements.append(
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=PALETTE[tag],
                   markersize=11, label=f"{LABEL_FULL[tag]} ({tag})"))
leg = ax.legend(handles=legend_elements, loc='lower left', fontsize=11,
                frameon=True, edgecolor='#E2E8F0', facecolor='white',
                title=None, ncol=2, columnspacing=1.2, handletextpad=0.6)
leg.get_frame().set_linewidth(0.8)

# 气泡大小说明
ax.text(0.98, 0.02, '气泡大小 = 评论规模', transform=ax.transAxes,
        fontsize=9, color='#94A3B8', ha='right', va='bottom')

# ── 右：四张分类卡片 ──
ax_r = fig.add_subplot(gs[0, 1])
ax_r.axis('off')

card_data = []
for tag in legend_order:
    cid = [k for k, v in cluster_labels.items() if tag in v][0]
    n_countries = cluster_profiles.loc[cid, '国家数']
    avg_review = cluster_profiles.loc[cid, '平均评论数']
    members = country_features[country_features['cluster'] == cid].nlargest(3, '评论数')['buyerCountry'].tolist()
    card_data.append({
        'tag': tag, 'full': LABEL_FULL[tag], 'desc': LABEL_DESC[tag],
        'color': PALETTE[tag], 'n_countries': n_countries,
        'avg_review': avg_review, 'top3': ', '.join(members),
    })

# 绘制卡片
card_h = 0.185
card_gap = 0.02
card_top = 0.92

for i, c in enumerate(card_data):
    y0 = card_top - i * (card_h + card_gap)
    # 色条
    rect = plt.Rectangle((0.04, y0 - 0.008), 0.035, card_h, facecolor=c['color'],
                          transform=ax_r.transAxes, clip_on=False, zorder=2)
    ax_r.add_patch(rect)
    # 卡片背景
    rect_bg = plt.Rectangle((0.08, y0 - card_h), 0.88, card_h, facecolor='#F8FAFC',
                             edgecolor='#E2E8F0', linewidth=0.8, transform=ax_r.transAxes,
                             zorder=1)
    ax_r.add_patch(rect_bg)
    # 分类名
    ax_r.text(0.12, y0 - 0.03, f'{c["full"]} ({c["tag"]})', transform=ax_r.transAxes,
              fontsize=14, fontweight='bold', color='#1E293B', va='top')
    # 特征描述
    ax_r.text(0.12, y0 - 0.08, c['desc'], transform=ax_r.transAxes,
              fontsize=11.5, color='#64748B', va='top')
    # 数据
    ax_r.text(0.12, y0 - 0.135, f'{c["n_countries"]} 个国家 · 均值 {c["avg_review"]:.0f} 条 · TOP: {c["top3"]}',
              transform=ax_r.transAxes, fontsize=10, color='#94A3B8', va='top')

# 底部算法说明
ax_r.text(0.5, 0.01, 'ML 算法: KMeans + PCA 降维 · 与 LDA 主题聚类互补（文本 + 用户双维度）',
          transform=ax_r.transAxes, fontsize=10, color='#CBD5E1', ha='center', va='bottom')

# === 全局标题 ===
fig.suptitle('KMeans 国家分群 — 跨境电商消费市场聚类分析', fontsize=20, fontweight='bold',
             color='#1E293B', y=0.985)
fig.text(0.5, 0.96, f'PCA 降维可视化 · {len(country_features)} 个国家 · 4 个聚类',
         ha='center', fontsize=12, color='#94A3B8')

plt.subplots_adjust(top=0.93, bottom=0.02, left=0.04, right=0.99, wspace=0.03)
plt.savefig("../charts/kmeans_country_clusters.png", dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
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
