# -*- coding: utf-8 -*-
"""
文件名：time_series_forecast.py
功能：时序预测 — 国家×品类交叉线性回归预测下月评分
      补全课程项目阶段要求的"预测模型"
作者：梁思怡
创建日期：2026-07-09
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

print("=" * 60)
print("  时序预测 — 国家×品类交叉线性回归")
print("=" * 60)

# ============ 1. 加载数据 ============
CSV_PATH = "../data/aliexpress_reviews.csv"
df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
df['productId'] = df['productId'].astype(str).str.replace('﻿', '').str.strip()
df['buyerCountry'] = df['buyerCountry'].astype(str).str.strip()

PRODUCT_NAMES = {
    "3256808363596774": "蓝牙耳机", "3256807406290815": "手机壳",
    "3256807087680846": "LED小夜灯", "3256807145227935": "连衣裙",
    "3256805677493085": "油壶",
}
PRODUCT_COLORS = {
    "蓝牙耳机":"#1677FF","手机壳":"#F53F3F","LED小夜灯":"#FF7D00",
    "连衣裙":"#722ED1","油壶":"#2E9B70",
}
CN_MAP = {'ES':'西班牙','US':'美国','UA':'乌克兰','FR':'法国'}

df['product_name'] = df['productId'].map(PRODUCT_NAMES)
df['month'] = pd.to_datetime(df['evalDate'], format='%d %b %Y', errors='coerce').dt.strftime('%Y-%m')

TARGET_COUNTRIES = ['ES','US','UA']  # KMeans成熟高价值市场TOP3
MONTHS_ALL = sorted(df['month'].unique())

print(f"\n[1/4] 数据构建完成，目标国家: {', '.join(CN_MAP[c] for c in TARGET_COUNTRIES)}")

# ============ 2. 每个 国家×品类 做线性回归 ============
print(f"\n[2/4] 各 国家×品类 线性回归预测...\n")

ALL_RESULTS = {}  # {country_code: [results_per_product]}

for country in TARGET_COUNTRIES:
    cdf = df[df['buyerCountry'] == country]
    results = []
    for pname in PRODUCT_NAMES.values():
        pcdf = cdf[cdf['product_name'] == pname].groupby('month')['starRating'].mean().reset_index()
        pcdf.columns = ['month','avg_rating']
        pcdf = pcdf.sort_values('month').set_index('month').reindex(MONTHS_ALL).reset_index()
        pcdf['avg_rating'] = pcdf['avg_rating'].interpolate(limit_direction='forward', limit_area='inside')
        pcdf = pcdf.dropna(subset=['avg_rating'])  # 去掉两端无法插值的外推月
        if len(pcdf) < 6:  # 至少6个有效月才做回归
            results.append({'name':pname,'valid':False})
            continue
        X = np.array(range(len(pcdf))).reshape(-1,1)
        y = pcdf['avg_rating'].values
        m = LinearRegression().fit(X, y)
        y_pred = m.predict(X)
        next_pred = m.predict(np.array([[len(pcdf)]]))[0]
        next_pred = float(np.clip(next_pred, 1.0, 5.0))  # 限幅[1,5]
        slope = m.coef_[0]
        r2 = m.score(X, y)
        direction = '↑' if slope>0.005 else ('↓' if slope<-0.005 else '→')
        results.append({'name':pname,'valid':True,'data':pcdf,'y_pred':y_pred,
                        'next_pred':next_pred,'slope':slope,'r2':r2,'direction':direction})
        print(f"  {CN_MAP[country]}+{pname}: 预测8月={next_pred:.2f} 斜率={slope:+.4f} R^2={r2:.3f} {direction}")
    ALL_RESULTS[country] = results

# ============ 3. 可视化 ============
print(f"\n[3/4] 生成预测图表...")

fig, axes = plt.subplots(2, 2, figsize=(20, 12))
fig.suptitle('国家 × 品类 交叉时序预测 — Top3高价值市场', fontsize=20, fontweight='bold', color='#0F172A')

for idx, country in enumerate(TARGET_COUNTRIES):
    ax = axes[idx//2][idx%2]
    cname = CN_MAP[country]
    results = ALL_RESULTS[country]

    for r in results:
        if not r['valid']:
            continue
        c = PRODUCT_COLORS[r['name']]
        months = r['data']['month'].tolist()
        ratings = r['data']['avg_rating'].values

        # 实际线
        ax.plot(months, ratings, color=c, marker='o', linewidth=1.8, markersize=5,
                markerfacecolor='white', markeredgewidth=1.5, zorder=3, alpha=0.85)
        # 回归虚线
        ax.plot(months, r['y_pred'], color=c, linewidth=1.3, linestyle='--', alpha=0.5, zorder=2)
        # 预测菱形
        ax.scatter('2026-08', r['next_pred'], color=c, marker='D', s=80, zorder=5,
                   edgecolors='white', linewidth=1.0)
        ax.annotate(f'{r["next_pred"]:.1f}', ('2026-08', r['next_pred']),
                    textcoords="offset points", xytext=(8, 0),
                    ha='left', fontsize=9, fontweight='bold', color=c)

    ax.set_title(f'{cname} ({country}) — 各品类月度评分趋势与预测', fontsize=14, fontweight='bold', color='#1E293B')
    ax.set_ylim(2.5, 5.0)
    ax.tick_params(axis='x', rotation=45, labelsize=9, colors='#333')
    ax.tick_params(axis='y', labelsize=9, colors='#333')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#999')
    ax.spines['bottom'].set_color('#999')
    ax.grid(axis='y', color='#EEE', linewidth=0.5)
    # 图例
    handles = [plt.Line2D([0],[0],color=PRODUCT_COLORS[p],linewidth=2) for p in PRODUCT_NAMES.values()]
    ax.legend(handles, list(PRODUCT_NAMES.values()), fontsize=9, loc='lower left',
              ncol=3, frameon=True, edgecolor='#CCC')

# 右下：结论
ax_c = axes[1][1]
ax_c.axis('off')
lines = [
    "国家 × 品类交叉预测结论",
    "",
    "西班牙 (ES):",
    "油壶/手机壳评分坚挺，蓝牙耳机下降",
    "LED灯波动大，连衣裙小幅回升",
    "",
    "美国 (US):",
    "LED灯/蓝牙耳机评分持续下降",
    "连衣裙高评分但数据稀少",
    "",
    "乌克兰 (UA):",
    "蓝牙耳机高分坚挺，手机壳小幅上升",
    "各品类评分均较高，市场质量好",
    "",
    "模型: sklearn LinearRegression",
    "月度趋势 + 线性回归 · 仅作趋势参考",
]
for i, line in enumerate(lines):
    if i == 0:
        fs, fw, fc = 15, 'bold', '#1E293B'
    elif line.startswith(('西班牙','美国','乌克兰')):
        fs, fw, fc = 13, 'bold', '#333333'
    elif line == "":
        continue
    else:
        fs, fw, fc = 11, 'normal', '#555555'
    ax_c.text(0.05, 0.94 - i*0.05, line, fontsize=fs, fontweight=fw, color=fc,
              transform=ax_c.transAxes, va='top')

fig.text(0.5, 0.005, '注: 红色菱形=8月预测 · 虚线=线性回归趋势线 · 仅作方向参考',
         ha='center', fontsize=12, fontweight='bold', color='#555555')

plt.tight_layout(rect=[0, 0.04, 1, 0.94])
plt.savefig("../charts/time_series_forecast.png", dpi=150, bbox_inches='tight', facecolor='white')
print("   时序预测图已保存: charts/time_series_forecast.png")

# ============ 4. 结论 ============
print(f"\n[4/4] 分析结论")
for country in TARGET_COUNTRIES:
    for r in ALL_RESULTS[country]:
        if r['valid']:
            print(f"   {CN_MAP[country]}+{r['name']}: 8月={r['next_pred']:.2f} {r['direction']}")
print(f"\n{'=' * 60}")
print("  时序预测完成")
print("=" * 60)
