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
from matplotlib.gridspec import GridSpec

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

topics = {
    "主题1\n尺寸不符": {"small":0.15, "size":0.14, "low":0.10, "looks":0.09, "big":0.08, "thought":0.07, "smaller":0.06, "light":0.05},
    "主题2\n商品损坏": {"work":0.13, "doesn":0.11, "arrived":0.10, "broken":0.10, "box":0.08, "bad":0.08, "came":0.07, "damaged":0.07},
    "主题3\n音质/质量差": {"quality":0.16, "sound":0.14, "poor":0.12, "terrible":0.09, "earphone":0.08, "recommend":0.06, "working":0.06, "poor quality":0.05},
    "主题4\n材质廉价": {"received":0.12, "cheap":0.11, "color":0.10, "photo":0.09, "plastic":0.09, "won":0.08, "case":0.07, "broke":0.06},
    "主题5\n适配错误": {"didn":0.12, "good":0.11, "fit":0.11, "don":0.10, "ordered":0.08, "arrived":0.07, "iphone":0.06, "item":0.05},
}
topic_labels = list(topics.keys())

fig = plt.figure(figsize=(18, 10))
gs = GridSpec(2, 4, width_ratios=[1, 1, 1, 1.4], figure=fig)
fig.suptitle("LDA 主题模型 — 负面评论痛点聚类分析", fontsize=16, fontweight='bold', x=0.5)

# 上排：前3个主题 (0,0) (0,1) (0,2)
for idx, (label, words) in enumerate(topics.items()):
    if idx < 3:
        row, col = 0, idx
    else:
        row, col = 1, idx - 3  # 下排：第4和第5个主题 (1,0) (1,1)

    ax = fig.add_subplot(gs[row, col])
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

# 分析结论框，占第4列（宽1.4倍）上下两行
ax_conclusion = fig.add_subplot(gs[:, 3])
ax_conclusion.axis('off')
conclusion = ("\n\n  LDA 无监督聚类分析结论\n\n"
    "  *  从 1,787 条低分评论自动发现 5 个痛点主题\n\n"
    "  *  蓝牙耳机: 音质差 & 商品损坏 (各 250 条)\n\n"
    "  *  LED 灯: 尺寸太小 / 与图片不符 (249 条)\n\n"
    "  *  手机壳: 材质廉价 & 适配错误 (87 / 84 条)\n\n"
    "  *  油壶: 到货损坏 & 材质廉价\n\n"
    "  *  连衣裙: 适配错误 & 尺寸不符\n\n"
    "  样本标准: starRating <= 2 且有英文翻译评论\n"
    "  模型困惑度: 388.5")

ax_conclusion.text(0.06, 1.0, conclusion, fontsize=11, transform=ax_conclusion.transAxes,
                verticalalignment='top', linespacing=1.5,
                bbox=dict(boxstyle='round,pad=0.8', facecolor='#f8f9fa', edgecolor='#ccd0d5', linewidth=1.5))

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig("../charts/lda_topics.png", dpi=150, bbox_inches='tight')
print("LDA 可视化已保存: charts/lda_topics.png")
