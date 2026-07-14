# -*- coding: utf-8 -*-
"""
文件名：kmeans_country_cluster.py
功能：KMeans 国家分群 — 102个国家按消费行为聚成4类市场画像
      补全课程核心阶段要求的 ML 分类算法
作者：梁思怡
创建日期：2026-07-09
"""
import pandas as pd
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
# 4. PCA + 可视化
# ============================================================
print(f"\n[4/5] PCA 降维可视化...")

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
country_features['pca_x'] = X_pca[:, 0]
country_features['pca_y'] = X_pca[:, 1]

TAG_COLOR = {
    'Star': '#5B3F9E',   # 深紫 — 成熟高价值
    'Box':  '#D68B2C',   # 暖橙 — 价格敏感大市场
    'Seed': '#2E9B70',   # 墨绿 — 潜力精品
    'Zoom': '#333333',   # 灰蓝 — 长尾探索
}
TAG_NAME = {
    'Star': '成熟高价值市场', 'Box': '价格敏感大市场',
    'Seed': '潜力精品市场',   'Zoom': '长尾探索市场',
}
TAG_DESC = {
    'Star': '高评分·高活跃 — 推荐重点投入',
    'Box':  '高活跃·中评分 — 价格/物流主导',
    'Seed': '高评分·低活跃 — 适合新品试水',
    'Zoom': '低活跃·低评分 — 暂不推荐',
}

# ---- 把 cluster ID 映射到业务标签 ----
cid_tag = {}
for cid in range(4):
    r = cluster_profiles.loc[cid]
    if r['平均星评'] >= cluster_profiles['平均星评'].median() and r['平均评论数'] >= cluster_profiles['平均评论数'].median():
        cid_tag[cid] = 'Star'
    elif r['平均评论数'] >= cluster_profiles['平均评论数'].median():
        cid_tag[cid] = 'Box'
    elif r['平均星评'] >= cluster_profiles['平均星评'].median():
        cid_tag[cid] = 'Seed'
    else:
        cid_tag[cid] = 'Zoom'

country_features['tag'] = country_features['cluster'].map(cid_tag)

# ---- 画布 ----
fig = plt.figure(figsize=(20, 9.2))

# 左右分割: 散点图(0~0.60) + 卡片列(0.64~0.92)
ax = fig.add_axes([0.05, 0.10, 0.54, 0.78])
ax_r = fig.add_axes([0.63, 0.10, 0.34, 0.78])

# ======== 左侧: PCA 散点图 ========
# 气泡大小
size_raw = country_features['评论数'].clip(upper=800)
sizes = 20 + size_raw / size_raw.max() * 320

for cid in range(4):
    mask = country_features['cluster'] == cid
    ax.scatter(country_features.loc[mask, 'pca_x'],
               country_features.loc[mask, 'pca_y'],
               s=sizes[mask], c=TAG_COLOR[cid_tag[cid]],
               alpha=0.78, edgecolors='white', linewidth=0.4, zorder=2)

# TOP2 标注 — 标签颜色跟随聚类，只标2个避免拥挤
for cid in range(4):
    mask = country_features['cluster'] == cid
    top2 = country_features[mask].nlargest(2, '评论数')
    for _, row in top2.iterrows():
        ax.annotate(row['buyerCountry'],
                    (row['pca_x'], row['pca_y']),
                    fontsize=9.5, fontweight='bold',
                    color=TAG_COLOR[cid_tag[cid]],
                    ha='left', va='bottom',
                    xytext=(6, 6), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                              edgecolor='none', alpha=0.88))

# 坐标轴
ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)',
              fontsize=14, fontweight='bold', color='#111111', labelpad=10)
ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)',
              fontsize=14, fontweight='bold', color='#111111', labelpad=10)
ax.tick_params(labelsize=11, colors='#111111', pad=4)
for spine in ['top','right']:
    ax.spines[spine].set_visible(False)
ax.spines['left'].set_color('#555555')
ax.spines['bottom'].set_color('#555555')
ax.set_axisbelow(True)
ax.yaxis.grid(True, color='#DDDDDD', linewidth=0.6)
# 右下角气泡说明
ax.text(0.98, 0.025, '● 大小 = 评论规模', transform=ax.transAxes,
        fontsize=9, color='#333333', ha='right', va='bottom')

# ======== 右侧: 四张业务卡片（色点+三级信息，代替图例）=======
ax_r.axis('off')

BUSINESS_RANK = ['Star', 'Box', 'Seed', 'Zoom']
# 国家代码→中文翻译（仅卡片使用，散点图不变）
CN_MAP = {'ES':'西班牙','UA':'乌克兰','FR':'法国','US':'美国','GB':'英国','KR':'韩国','BR':'巴西','IT':'意大利','MX':'墨西哥','PL':'波兰','DE':'德国','RU':'俄罗斯','NL':'荷兰','TR':'土耳其','JP':'日本','IL':'以色列','CL':'智利','CA':'加拿大','AU':'澳大利亚','PT':'葡萄牙','BE':'比利时','SE':'瑞典','AT':'奥地利','MZ':'莫桑比克','ET':'埃塞俄比亚','TH':'泰国','BY':'白俄罗斯','NG':'尼日利亚','VN':'越南','OM':'阿曼','AL':'阿尔巴尼亚','MK':'北马其顿','PA':'巴拿马','AR':'阿根廷','CO':'哥伦比亚','PE':'秘鲁','ZA':'南非','SG':'新加坡','CZ':'捷克','RO':'罗马尼亚','HU':'匈牙利','GR':'希腊','DK':'丹麦','NO':'挪威','FI':'芬兰','IE':'爱尔兰','NZ':'新西兰','SA':'沙特','AE':'阿联酋','PH':'菲律宾','MY':'马来西亚','ID':'印度尼西亚','KE':'肯尼亚','MA':'摩洛哥','EG':'埃及','BG':'保加利亚','HR':'克罗地亚','SK':'斯洛伐克','SI':'斯洛文尼亚','LT':'立陶宛','LV':'拉脱维亚','EE':'爱沙尼亚','CY':'塞浦路斯','MT':'马耳他','LU':'卢森堡','IS':'冰岛'}
for i, tag in enumerate(BUSINESS_RANK):
    cid = [k for k, v in cid_tag.items() if v == tag][0]
    c = TAG_COLOR[tag]
    star = cluster_profiles.loc[cid, '平均星评']
    n_ctry = int(cluster_profiles.loc[cid, '国家数'])
    n_rev = cluster_profiles.loc[cid, '平均评论数']
    top3_codes = country_features[country_features['cluster'] == cid].nlargest(3, '评论数')['buyerCountry'].tolist()
    top3_cn = '/'.join(CN_MAP.get(code, code) for code in top3_codes)

    y_top = 0.94 - i * 0.22

    # 卡片背景（窄一些，宽度0.85）
    rect = plt.Rectangle((0.0, y_top - 0.20), 0.85, 0.19, facecolor='#F4F4F4', edgecolor='#999999', linewidth=0.7, transform=ax_r.transAxes, zorder=0)
    ax_r.add_patch(rect)

    # L1: ●圆点 + 分类名（同行）
    ax_r.plot(0.06, y_top - 0.035, 'o', color=c, markersize=14, transform=ax_r.transAxes, clip_on=False)
    ax_r.text(0.14, y_top - 0.035, TAG_NAME[tag], transform=ax_r.transAxes, fontsize=16, fontweight='bold', color='#1E293B', va='center')
    # L2: 特征描述
    ax_r.text(0.14, y_top - 0.095, TAG_DESC[tag], transform=ax_r.transAxes, fontsize=12, color='#333333', va='center')
    # L3: 数据（TOP国家翻译为中文）
    ax_r.text(0.14, y_top - 0.155, f'{n_ctry}国 · 均{n_rev:.0f}评 · 星评{star:.2f} · TOP: {top3_cn}', transform=ax_r.transAxes, fontsize=11, color='#555555', va='center')

# 底部算法注释
ax_r.text(0.5, 0.01, 'ML: KMeans + PCA  ·  与 LDA 构成文本 + 用户双维度聚类',
          transform=ax_r.transAxes, fontsize=9, color='#555555', ha='center')

# ======== 全局标题 ========
fig.suptitle('KMeans 国家分群 — 跨境电商消费市场聚类分析',
             fontsize=21, fontweight='bold', color='#0F172A', y=1.015)
fig.text(0.5, 0.955, f'PCA 降维可视化  ·  {len(country_features)} 个国家  ·  K=4 聚类  ·  气泡 = 评论规模',
         ha='center', fontsize=12, color='#1E293B')

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
