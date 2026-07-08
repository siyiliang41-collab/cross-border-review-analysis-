# -*- coding: utf-8 -*-
"""
文件名：plot_lda_viz.py
功能：LDA 主题模型结果可视化
作者：梁思怡
日期：2026-07-08
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

topics = {
    "主题1\n尺寸不符": {"small":0.15, "size":0.14, "low":0.10, "looks":0.09, "big":0.08, "thought":0.07, "smaller":0.06, "light":0.05},
    "主题2\n商品损坏": {"work":0.13, "doesn":0.11, "arrived":0.10, "broken":0.10, "box":0.08, "bad":0.08, "came":0.07, "damaged":0.07},
    "主题3\n音质/质量差": {"quality":0.16, "sound":0.14, "poor":0.12, "terrible":0.09, "earphone":0.08, "recommend":0.06, "working":0.06, "poor quality":0.05},
    "主题4\n材质廉价": {"received":0.12, "cheap":0.11, "color":0.10, "photo":0.09, "plastic":0.09, "won":0.08, "case":0.07, "broke":0.06},
    "主题5\n适配错误": {"didn":0.12, "good":0.11, "fit":0.11, "don":0.10, "ordered":0.08, "arrived":0.07, "iphone":0.06, "item":0.05},
}

pain_data = {
    "尺寸不符":    [0,  249, 0,   0,  35],
    "商品损坏":    [250,185, 0,   55, 0],
    "音质/质量差": [250,0,   61,  40, 0],
    "材质廉价":    [0,  0,   87,  36, 45],
    "适配错误":    [125,141, 83,  0,  57],
}
products = ["蓝牙耳机", "LED小夜灯", "手机壳", "油壶", "连衣裙"]

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle("LDA 主题模型 — 负面评论痛点聚类分析", fontsize=16, fontweight='bold')

# 5个主题词频柱状图
for ax, (label, words) in zip(axes.flatten()[:5], topics.items()):
    names = list(words.keys())
    values = list(words.values())
    colors = ['#1565c0','#1976d2','#1e88e5','#2196f3','#42a5f5','#64b5f6','#90caf9','#bbdefb']
    bars = ax.barh(range(len(names)), values, color=colors)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=10)
    ax.set_title(label, fontsize=12, fontweight='bold')
    ax.invert_yaxis()
    ax.set_xlim(0, max(values)*1.3)
    for bar, val in zip(bars, values):
        ax.text(bar.get_width()+0.002, bar.get_y()+bar.get_height()/2, f'{val:.2f}', va='center', fontsize=9)

# 右下第6格 — 宽大的分析结论框
axes[1, 2].axis('off')
conclusion = ("\n\n  LDA 分析结论\n\n"
    "  *  从 1,787 条低分评论中,\n"
    "     LDA 自动聚类出 5 个痛点主题\n\n"
    "  *  蓝牙耳机最大痛点:\n"
    "     音质差 & 商品损坏 (各 250 条)\n\n"
    "  *  LED 灯主要投诉:\n"
    "     尺寸太小 / 与图片不符 (249 条)\n\n"
    "  *  手机壳主要投诉:\n"
    "     材质廉价 & iPhone 适配错误\n\n"
    "  *  油壶投诉集中在:\n"
    "     到货损坏 & 材质廉价\n\n"
    "  *  无监督 ML 成功落地,\n"
    "     满足课程核心阶段要求")

axes[1, 2].text(0.05, 0.95, conclusion, fontsize=12, transform=axes[1, 2].transAxes,
                verticalalignment='top', linespacing=2.0,
                bbox=dict(boxstyle='round,pad=1.2', facecolor='#f8f9fa', edgecolor='#ccd0d5', linewidth=1.5))

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig("../charts/lda_topics.png", dpi=150, bbox_inches='tight')
print("LDA 可视化已保存: charts/lda_topics.png")
