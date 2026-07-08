# -*- coding: utf-8 -*-
"""
文件名：plot_lda_viz.py
功能：LDA 主题模型结果可视化（v2 专业设计版）
作者：梁思怡
日期：2026-07-09
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# === 主题色 ===
C = {'topic1':'#1677FF', 'topic2':'#F53F3F', 'topic3':'#FF7D00',
     'topic4':'#86909C', 'topic5':'#722ED1'}

# === 关键词数据（已过滤噪声词，保留核心语义） ===
topics = [
    ("尺寸不符", C['topic1'],
     {"small":0.15,"size":0.14,"big":0.08,"smaller":0.06,"light":0.05,"low":0.10,"looks":0.09,"expected":0.05}),
    ("商品损坏", C['topic2'],
     {"broken":0.10,"damaged":0.07,"box":0.08,"came":0.07,"bad":0.08,"work":0.13,"arrived":0.10,"stopped":0.05}),
    ("音质/质量差", C['topic3'],
     {"quality":0.16,"sound":0.14,"poor":0.12,"poor quality":0.05,"terrible":0.09,"earphone":0.08,"sound quality":0.04,"headphones":0.06}),
    ("材质廉价", C['topic4'],
     {"cheap":0.11,"plastic":0.09,"color":0.10,"photo":0.09,"case":0.07,"broke":0.06,"material":0.05,"picture":0.05}),
    ("适配错误", C['topic5'],
     {"fit":0.11,"didn't fit":0.06,"ordered":0.08,"iphone":0.06,"item":0.05,"wrong":0.04,"size":0.05,"delivered":0.04}),
]

# === 各品类痛点数据 ===
pain_data = [
    ("蓝牙耳机", 250, 250, 125, 0, "音质差 & 商品损坏"),
    ("LED小夜灯", 249, 185, 141, 0, "尺寸太小/与图片不符"),
    ("手机壳", 0, 0, 83, 87, "材质廉价 & 适配错误"),
    ("油壶", 0, 55, 0, 36, "到货损坏 & 材质廉价"),
    ("连衣裙", 35, 0, 57, 45, "适配错误 & 尺寸不符"),
]

fig = plt.figure(figsize=(20, 9.5))
gs = GridSpec(2, 4, width_ratios=[1, 1, 1, 1.3], figure=fig, hspace=0.35, wspace=0.18)

# === 5 个主题词频图（上3下2，居中） ===
positions = [(0,0),(0,1),(0,2),(1,0),(1,1)]  # 第5个在 (1,2) 不放图
for idx, (name, color, words) in enumerate(topics):
    if idx < 5:
        ax = fig.add_subplot(gs[positions[idx]])
    else:
        break
    names = list(words.keys())
    values = list(words.values())
    bars = ax.barh(range(len(names)), values, color=color, height=0.65)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=11, color='#334155')
    ax.set_title(name, fontsize=13, fontweight='bold', color='#1E293B', pad=8)
    ax.invert_yaxis()
    ax.set_xlim(0, 0.20)
    ax.tick_params(left=False, bottom=False, labelsize=10, colors='#94A3B8')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#E2E8F0')
    ax.xaxis.grid(False)
    ax.yaxis.grid(False)
    for bar, val in zip(bars, values):
        ax.text(bar.get_width()+0.003, bar.get_y()+bar.get_height()/2,
                f'{val:.2f}', va='center', fontsize=9, color='#64748B')

# === 右下第5格：品类痛点条 ===
ax_pain = fig.add_subplot(gs[1, 2])
ax_pain.axis('off')
pain_colors = [C['topic1'], C['topic2'], C['topic3'], C['topic4'], C['topic5']]
topic_short = ['尺寸不符','商品损坏','音质/质量差','材质廉价','适配错误']

y_start = 0.92
for pi, (prod, *counts) in enumerate([p[:-1] for p in pain_data]):
    y = y_start - pi * 0.165
    ax_pain.text(0.02, y + 0.03, prod, fontsize=11, fontweight='bold', color='#1E293B')
    ax_pain.text(0.76, y + 0.03, pain_data[pi][5], fontsize=10, color='#64748B', ha='right')
    # mini bars
    total = sum(counts)
    x0 = 0.02
    for ci, cnt in enumerate(counts):
        if cnt > 0:
            w = cnt / max(250, total) * 0.30
            rect = plt.Rectangle((x0, y), w, 0.025, facecolor=pain_colors[ci], transform=ax_pain.transAxes)
            ax_pain.add_patch(rect)
            x0 += w + 0.005

ax_pain.text(0.02, y_start - len(pain_data)*0.165 - 0.02,
             f'样本: 1,787 条低分评论 (starRating ≤ 2)  ·  困惑度: 388.5  ·  n_components = 5',
             fontsize=9, color='#CBD5E1')

# === 右侧结论栏（跨两行） ===
ax_c = fig.add_subplot(gs[:, 3])
ax_c.axis('off')

conclusion_items = [
    (C['topic1'], "尺寸不符", "LED灯 (249)、连衣裙 (35)"),
    (C['topic2'], "商品损坏", "蓝牙耳机 (250)、LED灯 (185)、油壶 (55)"),
    (C['topic3'], "音质/质量差", "蓝牙耳机 (250)"),
    (C['topic4'], "材质廉价", "手机壳 (87)、油壶 (36)、连衣裙 (45)"),
    (C['topic5'], "适配错误", "手机壳 (84)、LED灯 (141)"),
]

y0 = 0.92
card_h = 0.12
for i, (color, name, desc) in enumerate(conclusion_items):
    y = y0 - i * card_h
    ax_c.plot(0.06, y, 'o', color=color, markersize=11, transform=ax_c.transAxes)
    ax_c.text(0.14, y, name, fontsize=13, fontweight='bold', color='#1E293B',
              va='center', transform=ax_c.transAxes)
    ax_c.text(0.14, y - 0.035, desc, fontsize=10, color='#64748B',
              va='center', transform=ax_c.transAxes)

# 底部技术说明
ax_c.text(0.06, 0.02, 'LDA 无监督聚类  ·  n=5  ·  困惑度 388.5  ·  短文本天然限制',
          fontsize=10, color='#CBD5E1', transform=ax_c.transAxes)

# === 全局标题 ===
fig.suptitle('LDA 主题模型 — 负面评论痛点聚类分析',
             fontsize=20, fontweight='bold', color='#1E293B', y=0.995)
fig.text(0.5, 0.975, '1,787 条低分评论 (starRating ≤ 2) · 5 个自动聚类主题 · 英文翻译文本',
         ha='center', fontsize=12, color='#94A3B8')

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig("../charts/lda_topics.png", dpi=150, bbox_inches='tight', facecolor='white')
print("LDA 可视化已保存: charts/lda_topics.png")
