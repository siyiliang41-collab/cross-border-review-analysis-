# -*- coding: utf-8 -*-
"""
文件名：time_series_forecast.py
功能：时序预测 — 基于13个月数据的线性回归预测下月评分
      补全课程项目阶段要求的"预测模型"
作者：梁思怡
创建日期：2026-07-09
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 1. 构建时序数据（从ads_monthly_trend等效取数）
# ============================================================
print("=" * 60)
print("  时序预测 — 线性回归预测下月评分趋势")
print("=" * 60)

# 月度趋势数据（来自 Spark SQL ads_monthly_trend 实际结果）
months = ['2025-07','2025-08','2025-09','2025-10','2025-11','2025-12',
          '2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07']
ratings = [4.22, 4.15, 4.16, 4.33, 4.38, 4.31,
           4.38, 4.36, 4.57, 3.97, 3.98, 3.93, 4.57]

# 月份序号作为X
X = np.array(range(len(months))).reshape(-1, 1)
y = np.array(ratings)

print(f"\n[1/4] 时序数据加载完成")
print(f"   数据点: {len(months)} 个月")
print(f"   评分范围: {min(ratings):.2f} ~ {max(ratings):.2f}")

# ============================================================
# 2. 线性回归训练
# ============================================================
print(f"\n[2/4] 线性回归建模...")

model = LinearRegression()
model.fit(X, y)
y_pred = model.predict(X)

# 预测下月
next_x = np.array([[len(months)]])
next_pred = model.predict(next_x)[0]
next_month = '2026-08'

slope = model.coef_[0]
r2 = model.score(X, y)

print(f"   斜率: {slope:.4f} 分/月")
print(f"   R^2: {r2:.4f}")
print(f"   预测 {next_month}: {next_pred:.2f} 分")

# ============================================================
# 3. 可视化
# ============================================================
print(f"\n[3/4] 生成预测图表...")

fig, ax = plt.subplots(figsize=(14, 6))
fig.suptitle('月度评分趋势预测 — 简单线性回归', fontsize=18, fontweight='bold', color='#0F172A')

# 历史数据点 + 折线
ax.plot(months, ratings, color='#1677FF', marker='o', linewidth=2.5, markersize=10,
        markerfacecolor='white', markeredgewidth=2, zorder=3, label='历史评分')
# 回归线
ax.plot(months, y_pred, color='#FF7A45', linewidth=2, linestyle='--', zorder=2, label=f'线性回归拟合 (R²={r2:.2f})')
# 预测点
ax.scatter(next_month, next_pred, color='#F53F3F', marker='D', s=180, zorder=5,
           edgecolors='white', linewidth=1.5, label=f'预测 {next_month}: {next_pred:.2f}分')
ax.annotate(f'{next_pred:.2f}', (next_month, next_pred), textcoords="offset points",
            xytext=(0, 18), ha='center', fontsize=14, fontweight='bold', color='#F53F3F')

# 美化
ax.set_ylabel('月均评分', fontsize=13, fontweight='bold', color='#111111')
ax.set_ylim(3.5, 5.0)
ax.tick_params(axis='x', rotation=45, labelsize=11, colors='#333333')
ax.tick_params(axis='y', labelsize=11, colors='#333333')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#999')
ax.spines['bottom'].set_color('#999')
ax.grid(axis='y', color='#EEEEEE', linewidth=0.8)
ax.legend(fontsize=12, loc='lower left', frameon=True, edgecolor='#CCC')

# 底部注释
fig.text(0.5, 0.01, f'模型: sklearn LinearRegression · 13个训练点 · 斜率 {slope:.4f} · 预测仅供参考，数据量有限',
         ha='center', fontsize=12, fontweight='bold', color='#555555')

plt.tight_layout(rect=[0, 0.05, 1, 0.94])
plt.savefig("../charts/time_series_forecast.png", dpi=150, bbox_inches='tight', facecolor='white')
print("   时序预测图已保存: charts/time_series_forecast.png")

# ============================================================
# 4. 结论
# ============================================================
print(f"\n[4/4] 分析结论")
print(f"   预测 {next_month} 月均评分: {next_pred:.2f}")
print(f"   趋势: {'上升' if slope > 0 else '下降'} (每10个月{'提高' if slope>0 else '降低'}{abs(slope)*10:.1f}分)")
print(f"   模型限制: 仅13个数据点，线性回归适合趋势参考，不适合精确预测")
print(f"\n{'=' * 60}")
print("  时序预测完成")
print("=" * 60)
