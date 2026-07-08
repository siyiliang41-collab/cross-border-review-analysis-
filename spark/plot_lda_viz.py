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

fig = plt.figure(figsize=(18, 9))
gs = GridSpec(2, 3, figure=fig)
fig.suptitle("LDA 主题模型 — 负面评论痛点聚类分析", fontsize=18, fontweight='bold', x=0.5)

# 5个主题词频图：上排3个 + 下排前2个
for idx, (label, words) in enumerate(topics.items()):
    if idx < 3:
        row, col = 0, idx
    else:
        row, col = 1, idx - 3  # (1,0) (1,1)

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

# 右下第6格 (1,2) — 分析结论，直接显示，字号加大加粗
ax_conclusion = fig.add_subplot(gs[1, 2])
ax_conclusion.axis('off')
conclusion_lines = [
    "LDA 无监督聚类分析结论",
    "",
    "从 1,787 条低分评论自动发现 5 个痛点主题",
    "",
    "蓝牙耳机: 音质差 & 商品损坏 (各 250 条)",
    "LED 灯: 尺寸太小 / 与图片不符 (249 条)",
    "手机壳: 材质廉价 & 适配错误 (87 / 84 条)",
    "油壶: 到货损坏 & 材质廉价",
    "连衣裙: 适配错误 & 尺寸不符",
    "",
    "样本: starRating ≤ 2 且有英文翻译评论",
    "困惑度: 388.5",
]
y_pos = 0.95
for i, line in enumerate(conclusion_lines):
    if i == 0:
        ax_conclusion.text(0.05, y_pos - i*0.07, line, fontsize=14, fontweight='bold',
                          color='#1E293B', transform=ax_conclusion.transAxes, va='top')
    elif line == "":
        continue
    elif i <= 2:
        ax_conclusion.text(0.05, y_pos - i*0.07, line, fontsize=12, fontweight='bold',
                          color='#333333', transform=ax_conclusion.transAxes, va='top')
    else:
        ax_conclusion.text(0.05, y_pos - i*0.07, line, fontsize=12,
                          color='#333333', transform=ax_conclusion.transAxes, va='top')

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig("../charts/lda_topics.png", dpi=150, bbox_inches='tight')
print("LDA 可视化已保存: charts/lda_topics.png")
