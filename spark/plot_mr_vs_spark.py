# -*- coding: utf-8 -*-
"""
文件名：plot_mr_vs_spark.py
功能：MR vs Spark 性能对比可视化（同台 YARN 竞技）
作者：梁思怡
日期：2026-07-08 | 更新：2026-07-09（同台YARN数据）
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 同台 YARN 竞技数据（2026-07-09 实测）
datasets = ['1,000 条', '10,000 条', '19,271 条']
mr_times   = [19.9, 20.8, 21.0]
spark_times = [2.2, 1.7, 1.7]
speedup    = [19.9/2.2, 20.8/1.7, 21.0/1.7]

fig = plt.figure(figsize=(18, 7.5))

# ===== 左: 并排柱状图 =====
ax1 = fig.add_axes([0.06, 0.20, 0.44, 0.65])
x = np.arange(len(datasets))
w = 0.35

b1 = ax1.bar(x - w/2, mr_times, w, color='#E65100', label='MapReduce (YARN)', edgecolor='white', linewidth=0.5)
b2 = ax1.bar(x + w/2, spark_times, w, color='#1565C0', label='Spark (YARN)', edgecolor='white', linewidth=0.5)

for bar in b1:
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.4, f'{bar.get_height():.1f}s',
             ha='center', fontsize=13, fontweight='bold', color='#E65100')
for bar in b2:
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.4, f'{bar.get_height():.1f}s',
             ha='center', fontsize=13, fontweight='bold', color='#1565C0')

ax1.set_ylabel('耗时 (秒)', fontsize=14, fontweight='bold', color='#1E293B')
ax1.set_xlabel('数据量', fontsize=13, fontweight='bold', color='#555', labelpad=6)
ax1.set_title('WordCount 耗时对比', fontsize=16, fontweight='bold', color='#0F172A', pad=12)
ax1.set_xticks(x)
ax1.set_xticklabels(datasets, fontsize=13, fontweight='bold', color='#333')
ax1.legend(fontsize=12, loc='upper left', framealpha=0.9)
ax1.tick_params(labelsize=12)
for sp in ['top', 'right']: ax1.spines[sp].set_visible(False)
ax1.grid(axis='y', alpha=0.12, linewidth=0.3)
ax1.set_ylim(0, 28)

# ===== 右: 加速比折线 =====
ax2 = fig.add_axes([0.56, 0.20, 0.40, 0.65])
ax2.plot(datasets, speedup, color='#2E7D32', marker='o', linewidth=3, markersize=14,
         markerfacecolor='white', markeredgewidth=2.5, markeredgecolor='#2E7D32')
for i, (d, s) in enumerate(zip(datasets, speedup)):
    ax2.annotate(f'{s:.1f}x', (d, s), textcoords='offset points', xytext=(0, 16),
                 ha='center', fontsize=15, fontweight='bold', color='#2E7D32')

ax2.set_ylabel('加速比 (MR / Spark)', fontsize=14, fontweight='bold', color='#1E293B')
ax2.set_xlabel('数据量', fontsize=13, fontweight='bold', color='#555', labelpad=6)
ax2.set_title('Spark 相对 MR 加速比', fontsize=16, fontweight='bold', color='#0F172A', pad=12)
ax2.grid(axis='y', alpha=0.12, linewidth=0.3)
ax2.set_ylim(0, 18)
ax2.tick_params(labelsize=12)
for sp in ['top', 'right']: ax2.spines[sp].set_visible(False)

# 底部注释（移到上方，留出足够空间）
fig.text(0.5, 0.06, '同台 YARN 集群竞技，MR 固定开销 ~20s（容器启动+调度+磁盘溢写），Spark on YARN 仅 1.7~2.2s，加速比 9~12 倍',
         ha='center', fontsize=13, fontweight='bold', color='#1E293B')

# 标题 — 拉开间距
fig.suptitle('MR vs Spark 同台 YARN 竞技 — WordCount 性能对比', fontsize=21, fontweight='bold', color='#0F172A', y=0.98)
fig.text(0.5, 0.91, '同一集群 · 同一数据 · 同一 WordCount 任务  |  YARN 1 节点 hadoop03',
         ha='center', fontsize=12, color='#666')

plt.savefig("../charts/mr_vs_spark.png", dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
print("MR vs Spark 对比图已保存: charts/mr_vs_spark.png")
