# -*- coding: utf-8 -*-
"""
文件名：plot_mr_vs_spark.py
功能：MR vs Spark 性能对比可视化
作者：梁思怡
日期：2026-07-08
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 实际跑出来的数据
datasets = ['1,000 条', '10,000 条', '19,271 条']
mr_times   = [22.162, 24.941, 23.860]
spark_times = [4.819, 0.968, 1.362]
speedup    = [22.162/4.819, 24.941/0.968, 23.860/1.362]

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
fig.suptitle('MR vs Spark WordCount 性能对比（3节点24GB YARN集群）', fontsize=16, fontweight='bold')

# 左图：并排柱状图
x = np.arange(len(datasets))
width = 0.35
bars1 = axes[0].bar(x - width/2, mr_times, width, label='MapReduce (YARN)', color='#ff6d00', edgecolor='white')
bars2 = axes[0].bar(x + width/2, spark_times, width, label='Spark (本地模式)', color='#2979ff', edgecolor='white')
axes[0].set_ylabel('耗时 (秒)')
axes[0].set_title('WordCount 耗时对比')
axes[0].set_xticks(x)
axes[0].set_xticklabels(datasets)
axes[0].legend(fontsize=11)
axes[0].grid(axis='y', alpha=0.3)

# 柱上标数值
for bar, val in zip(bars1, mr_times):
    axes[0].text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3, f'{val:.1f}s', ha='center', fontsize=11, fontweight='bold')
for bar, val in zip(bars2, spark_times):
    axes[0].text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3, f'{val:.1f}s', ha='center', fontsize=11, fontweight='bold')

# 右图：加速比折线
axes[1].plot(datasets, speedup, color='#00c853', marker='o', linewidth=3, markersize=12,
             markerfacecolor='white', markeredgewidth=2.5, markeredgecolor='#00c853')
axes[1].set_ylabel('加速比 (MR/Spark)')
axes[1].set_title('Spark 相对 MR 的加速比')
axes[1].grid(axis='y', alpha=0.3)
axes[1].set_ylim(0, 35)
for i, (d, s) in enumerate(zip(datasets, speedup)):
    axes[1].annotate(f'{s:.1f}x', (d, s), textcoords="offset points", xytext=(0,14),
                     ha='center', fontsize=13, fontweight='bold', color='#00c853')

# 底部结论文字
fig.text(0.5, 0.02, '结论: MR主要开销在YARN容器启动(~20s)；Spark首次冷启动后后续计算秒级完成。\nHive管元数据 + Spark做计算引擎是企业湖仓一体架构的最佳实践',
         ha='center', fontsize=12, color='#555', bbox=dict(boxstyle='round,pad=0.5', facecolor='#f5f5f5', edgecolor='#ddd'))

plt.tight_layout(rect=[0, 0.08, 1, 0.95])
plt.savefig("../charts/mr_vs_spark.png", dpi=150, bbox_inches='tight')
print("MR vs Spark 对比图已保存: charts/mr_vs_spark.png")
