# -*- coding: utf-8 -*-
"""
文件名：plot_mr_vs_spark.py
功能：MR vs Spark 性能对比可视化（v2 专业设计版）
作者：梁思怡
日期：2026-07-09
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# === 数据 ===
datasets = ['1,000 条', '10,000 条', '19,271 条']
mr_times    = [22.162, 24.941, 23.860]
spark_times = [4.819, 0.968, 1.362]
speedup     = [22.162/4.819, 24.941/0.968, 23.860/1.362]

# === 配色 ===
C_MR     = '#FF7A45'  # MapReduce 暖橙
C_SPARK  = '#1677FF'  # Spark 科技蓝
C_SPEED  = '#00B42A'  # 加速比墨绿
C_GRID   = '#F2F3F5'
C_TEXT   = '#1E293B'
C_MUTED  = '#94A3B8'

fig, axes = plt.subplots(1, 2, figsize=(16, 5.8))
fig.subplots_adjust(wspace=0.25, left=0.06, right=0.98, top=0.88)

# === 左图：柱状图 ===
ax = axes[0]
x = np.arange(len(datasets))
w = 0.32

b1 = ax.bar(x - w/2, mr_times, w, color=C_MR, edgecolor='white', linewidth=0.8, zorder=2)
b2 = ax.bar(x + w/2, spark_times, w, color=C_SPARK, edgecolor='white', linewidth=0.8, zorder=2)

ax.set_xticks(x)
ax.set_xticklabels(datasets, fontsize=12, color=C_TEXT)
ax.set_ylabel('耗时 (秒)', fontsize=12, color='#64748B', labelpad=10)
ax.set_title('WordCount 耗时对比', fontsize=14, fontweight='bold', color=C_TEXT, pad=12)
ax.tick_params(labelsize=10, colors=C_MUTED)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#E2E8F0')
ax.spines['bottom'].set_color('#E2E8F0')
ax.yaxis.grid(True, color=C_GRID, linewidth=0.8)
ax.set_axisbelow(True)

# 柱上数值
for bar, val in zip(b1, mr_times):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.4,
            f'{val:.1f}s', ha='center', fontsize=11, fontweight='bold', color=C_MR)
for bar, val in zip(b2, spark_times):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.4,
            f'{val:.1f}s', ha='center', fontsize=11, fontweight='bold', color=C_SPARK)

# 图例
legend1 = plt.Rectangle((0,0),1,1, fc=C_MR)
legend2 = plt.Rectangle((0,0),1,1, fc=C_SPARK)
ax.legend([legend1, legend2], ['MapReduce (YARN)', 'Spark (local[*])'],
          fontsize=11, loc='upper right', frameon=True, edgecolor='#E2E8F0',
          handlelength=1, handleheight=1.2, ncol=2, columnspacing=0.8)

# === 右图：加速比 ===
ax2 = axes[1]
ax2.plot(datasets, speedup, color=C_SPEED, marker='o', linewidth=3, markersize=14,
         markerfacecolor='white', markeredgewidth=3, markeredgecolor=C_SPEED, zorder=3)
ax2.set_ylabel('加速比 (MR / Spark)', fontsize=12, color='#64748B', labelpad=10)
ax2.set_title('Spark 相对 MR 的加速比', fontsize=14, fontweight='bold', color=C_TEXT, pad=12)
ax2.tick_params(labelsize=10, colors=C_MUTED)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['left'].set_color('#E2E8F0')
ax2.spines['bottom'].set_color('#E2E8F0')
ax2.set_ylim(0, 35)
ax2.yaxis.grid(True, color=C_GRID, linewidth=0.8)
ax2.set_axisbelow(True)

for d, s in zip(datasets, speedup):
    ax2.annotate(f'{s:.1f}x', (d, s), textcoords="offset points", xytext=(0, 16),
                 ha='center', fontsize=14, fontweight='bold', color=C_SPEED)

# === 底部注释 ===
fig.text(0.5, 0.02,
         '注：Spark 第1组(1k)含 JVM/SparkSession 冷启动开销 (~4s)，后续组复用内存。MR 固定开销约 20s (YARN 容器调度+序列化+磁盘溢写)，几乎不随数据量增长。',
         ha='center', fontsize=10, color=C_MUTED,
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#F7F8FA', edgecolor='#E2E8F0', linewidth=0.6))

# === 全局标题 ===
fig.suptitle('MR (YARN) vs Spark (local[*]) — WordCount 性能对比',
             fontsize=18, fontweight='bold', color=C_TEXT, y=0.985)

plt.tight_layout(rect=[0, 0.05, 1, 0.96])
plt.savefig("../charts/mr_vs_spark.png", dpi=150, bbox_inches='tight', facecolor='white')
print("MR vs Spark 对比图已保存: charts/mr_vs_spark.png")
