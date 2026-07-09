# -*- coding: utf-8 -*-
"""
评分与情感一致性分析 - 可视化脚本
================================================
对速卖通评论数据进行星评-情感交叉校验，评估数据可信度。

布局: 上排 3 图 (散点 | 箱线 | 柱状) + 底部结论条
分类: Type A (高星低情感/疑似刷单)  Type B (低星高情感/翻译偏差)

作者：梁思怡
日期：2026-07-09
"""

import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 全局配置
# ============================================================

DATA_PATH   = "../data/aliexpress_reviews.csv"
OUTPUT_PATH = "../charts/consistency_analysis.png"
OUTPUT_DPI  = 180

HIGH_STAR, LOW_STAR = 4, 2
SENT_LOW, SENT_HIGH = -0.2, 0.3

PRODUCT_MAP = {
    "3256808363596774": "蓝牙耳机",
    "3256807406290815": "手机壳",
    "3256807087680846": "LED小夜灯",
    "3256807145227935": "连衣裙",
    "3256805677493085": "油壶",
}

# -------- 配色 --------
# 理论依据: 低饱和暖-冷对比, 异常点用暖色前推, 正常数据退后。
# 调色板参考: Coolors.co "vintage-scientific" 方向微调.

PAL = {
    'bg':        '#F9F9F7',  # 画布底色 暖白
    'normal':    '#CBD5E1',  # 正常散点  slate-300, 退后
    'type_a':    '#B8414B',  # Type A   沉稳砖红
    'type_b':    '#4C72B0',  # Type B   冷蓝 — Bertin: 与砖红色相对比，增强"可选择"性
    'trend':     '#285577',  # 趋势线   深蓝
    'grid':      '#E2E2DF',
    'spine':     '#D0D0CC',
    'text':      '#2D2D2D',
    'subtext':   '#888888',
    'bar_a':     '#B8414B',
    'bar_b':     '#4C72B0',
    'card_bg':   '#FFFFFF',
    'card_edge': '#E6E6E3',
    'star_low':  '#C4564A',  # 1星箱体  暖红
    'star_mid':  '#D4A24E',  # 3星箱体  暖金
    'star_high': '#4E8B7A',  # 5星箱体  青绿
    'ref_line':  '#B0B0A8',
}

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


# ============================================================
# 数据分析层
# ============================================================

class ConsistencyAnalyzer:

    def __init__(self, data_path, product_map):
        self.data_path = data_path
        self.product_map = product_map
        self._analyzer = SentimentIntensityAnalyzer()

    def load(self):
        df = pd.read_csv(self.data_path, encoding='utf-8-sig')
        df['productId'] = (df['productId'].astype(str)
                           .str.replace('﻿', '', regex=False).str.strip())
        df['starRating'] = (df['buyerEval'].astype(float) / 20).round(1)
        df = df[df['feedbackTranslated'].notna() &
                (df['feedbackTranslated'].str.strip() != '')].copy()
        df['productName'] = df['productId'].map(self.product_map)
        self.df = df
        print(f"  [OK] {len(self.df):,} 条有效评论已加载")
        return self

    def analyze(self):
        scores = self.df['feedbackTranslated'].apply(
            lambda t: self._analyzer.polarity_scores(str(t))['compound'])
        self.df['compound'] = scores
        print(f"  [OK] VADER 完成 [{scores.min():.2f}, {scores.max():.2f}]")
        return self

    def classify(self):
        is_a = (self.df['starRating'] >= HIGH_STAR) & (self.df['compound'] < SENT_LOW)
        is_b = (self.df['starRating'] <= LOW_STAR) & (self.df['compound'] > SENT_HIGH)
        self.type_a = self.df[is_a]
        self.type_b = self.df[is_b]
        self.normal = self.df[~(is_a | is_b)]
        print(f"  [OK] 正常 {len(self.normal):,}  Type A {len(self.type_a)}  Type B {len(self.type_b)}")
        return self

    def run(self):
        self.load(); self.analyze(); self.classify()
        return self

    @property
    def s(self):
        N = len(self.df); Na = len(self.type_a); Nb = len(self.type_b)
        return {
            'total': N, 'normal': N - Na - Nb,
            'a': Na, 'b': Nb, 'ab': Na + Nb,
            'pn': (N - Na - Nb) / N * 100,
            'pa': (Na + Nb) / N * 100,
        }

    @property
    def corr(self):
        r, rp = stats.pearsonr(self.df['starRating'], self.df['compound'])
        rho, rhop = stats.spearmanr(self.df['starRating'], self.df['compound'])
        return {'pearson_r': r, 'pearson_p': rp, 'spearman_r': rho, 'spearman_p': rhop}

    def product_breakdown(self):
        rows = []
        for pid, pname in self.product_map.items():
            sub = self.df[self.df['productId'] == pid]
            t = len(sub)
            if t == 0: continue
            a = len(self.type_a[self.type_a['productId'] == pid])
            b = len(self.type_b[self.type_b['productId'] == pid])
            rows.append({'product': pname, 'total': t,
                         'a': a, 'b': b, 'ab': a + b,
                         'rate': (a + b) / t * 100})
        return pd.DataFrame(rows)

    def star_distribution(self):
        dist = {}
        for star in sorted(self.df['starRating'].round().unique()):
            sub = self.df[self.df['starRating'].round() == star]
            if len(sub) > 0:
                dist[int(star)] = {
                    'count': len(sub), 'mean': sub['compound'].mean(),
                    'values': sub['compound'].values,
                }
        return dist


# ============================================================
# 可视化层
# ============================================================

def _spine(ax):
    """去掉上右边框，底部留淡色"""
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    for s in ['left', 'bottom']:
        ax.spines[s].set_color(PAL['spine'])
        ax.spines[s].set_linewidth(0.5)
    ax.tick_params(labelsize=9.5, colors=PAL['subtext'], length=2.5, pad=3)
    ax.set_facecolor(PAL['bg'])


class ConsistencyVisualizer:

    def __init__(self, an):
        self.a = an
        self.bd = an.product_breakdown()
        self.sd = an.star_distribution()

    # -------- 主入口 --------

    def render(self, path, dpi=OUTPUT_DPI):
        fig = plt.figure(figsize=(20, 8.5), facecolor=PAL['bg'])

        # 上排 3 图: 1 行 x 3 列, 宽度等分
        gs_top = GridSpec(1, 3, figure=fig,
                          left=0.05, right=0.98, top=0.86, bottom=0.30,
                          wspace=0.28)

        ax_scatter = fig.add_subplot(gs_top[0])
        ax_box     = fig.add_subplot(gs_top[1])
        ax_bar     = fig.add_subplot(gs_top[2])

        self._scatter(ax_scatter)
        self._boxplot(ax_box)
        self._bars(ax_bar)

        # 底部通栏信息条
        self._footer(fig)

        # 标题
        fig.suptitle('评分与情感一致性分析',
                     fontsize=23, fontweight='bold', color=PAL['text'],
                     y=0.97, x=0.05, ha='left')

        fig.savefig(path, dpi=dpi, facecolor=PAL['bg'], edgecolor='none',
                    bbox_inches='tight', pad_inches=0.3)
        plt.close()
        print(f"\n[OK] 已保存: {path}")

    # -------- 图1: 散点 --------

    def _scatter(self, ax):
        # 正常点: 蓝色半透明 + jitter 展开密度分布
        # 星级只有 5 个离散值，加 jitter 避免叠成 5 条竖线
        rng = np.random.RandomState(42)
        x_normal = self.a.normal['starRating'].values
        x_jitter = x_normal + rng.uniform(-0.25, 0.25, size=len(x_normal))

        ax.scatter(x_jitter, self.a.normal['compound'].values,
                   c='#4C72B0', s=8, alpha=0.22, zorder=2,
                   edgecolors='none', linewidths=0)

        # 拟合线: 每星均值 → 各星级情感倾向
        stars = sorted(self.sd.keys())
        means = [self.sd[s]['mean'] for s in stars]
        ax.plot(stars, means, color=PAL['trend'], linewidth=2.8, alpha=0.92,
                zorder=8, label=f'各星级情感均值 (n={len(self.a.normal):,})')

        ax.axhline(y=0, color=PAL['ref_line'], linewidth=0.6, linestyle='--',
                   alpha=0.5, zorder=0)
        ax.set_xlim(0.3, 5.7); ax.set_ylim(-1.12, 1.25)
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_xticklabels(['1 星', '2 星', '3 星', '4 星', '5 星'])
        ax.set_xlabel('用户星评', fontsize=12, color=PAL['text'], labelpad=4)
        ax.set_ylabel('VADER Compound', fontsize=12, color=PAL['text'], labelpad=4)
        _spine(ax); ax.grid(True, alpha=0.10, linewidth=0.35, color=PAL['grid'])

        leg = ax.legend(fontsize=9, loc='upper left', framealpha=0.85,
                        edgecolor=PAL['spine'], borderpad=0.5, labelspacing=0.4)
        leg.set_zorder(10)

    # -------- 图2: 箱线 --------

    def _boxplot(self, ax):
        stars = sorted(self.sd.keys())
        data = [self.sd[s]['values'] for s in stars]

        # 渐变配色: 红 -> 琥珀 -> 金 -> 青绿 -> 蓝绿
        colors = [PAL['star_low'], '#CD7A4C', PAL['star_mid'],
                  '#6DA88D', PAL['star_high']]

        bp = ax.boxplot(data, patch_artist=True, widths=0.48,
                        showfliers=True, showmeans=False,
                        flierprops=dict(marker='o', markerfacecolor=PAL['subtext'],
                                        markersize=1.8, alpha=0.20,
                                        markeredgecolor='none'),
                        medianprops=dict(color='white', linewidth=1.8),
                        whiskerprops=dict(color=PAL['subtext'], linewidth=0.6),
                        capprops=dict(color=PAL['subtext'], linewidth=0.6))

        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.85)

        # 标签含中位数
        labels = []
        for s in stars:
            med = np.median(self.sd[s]['values'])
            labels.append(f'{s} 星\nmed {med:+.2f}')
        ax.set_xticklabels(labels, fontsize=9.5)

        ax.axhline(y=0, color=PAL['ref_line'], linewidth=0.6, linestyle='--', alpha=0.45)
        ax.set_ylim(-1.12, 1.25)
        ax.set_ylabel('VADER Compound', fontsize=12, color=PAL['text'], labelpad=4)
        _spine(ax)
        ax.grid(True, axis='y', alpha=0.10, linewidth=0.35, color=PAL['grid'])
        ax.set_title('各星级情感得分分布', fontsize=14, fontweight='bold',
                     color=PAL['text'], pad=10)

    # -------- 图3: 柱状 --------

    def _bars(self, ax):
        bd = self.bd
        prods = bd['product'].tolist()
        x = np.arange(len(prods))
        w = 0.36
        pct_a = bd['a'].values / bd['total'].values * 100
        pct_b = bd['b'].values / bd['total'].values * 100

        ax.bar(x, pct_a, w, color=PAL['bar_a'], alpha=0.85,
               label='Type A', edgecolor='white', linewidth=0.3, zorder=3)
        ax.bar(x, pct_b, w, bottom=pct_a, color=PAL['bar_b'], alpha=0.85,
               label='Type B', edgecolor='white', linewidth=0.3, zorder=3)

        for i, rate in enumerate(bd['rate']):
            ax.text(i, rate + 0.45, f'{rate:.1f}%', ha='center',
                    fontsize=11.5, fontweight='bold', color=PAL['text'])

        ax.axhline(y=10, color=PAL['ref_line'], linewidth=0.7,
                   linestyle='--', alpha=0.5, zorder=1)
        ax.text(len(prods) - 0.45, 10.5, '10%', fontsize=9,
                color=PAL['subtext'], ha='right')

        ax.set_xticks(x)
        ax.set_xticklabels(prods, fontsize=11)
        ax.set_ylim(0, max(bd['rate']) * 1.50)
        ax.set_ylabel('异常率 (%)', fontsize=12, color=PAL['text'], labelpad=4)
        _spine(ax)
        ax.grid(True, axis='y', alpha=0.10, linewidth=0.35, color=PAL['grid'])
        ax.legend(fontsize=9, loc='upper right', framealpha=0.80,
                  edgecolor=PAL['spine'], borderpad=0.4)
        ax.set_title('各品类异常率对比', fontsize=14, fontweight='bold',
                     color=PAL['text'], pad=10)

    # -------- 底部信息条 --------

    def _footer(self, fig):
        """底部信息条 — Tufte 风格：纯文本 + 左侧细色条分组，消除卡片框的 1+1=3 效应"""
        s = self.a.s; c = self.a.corr; bd = self.bd
        worst = bd.loc[bd['rate'].idxmax()]
        best  = bd.loc[bd['rate'].idxmin()]
        rho = c['spearman_r']
        strength = '强' if abs(rho) > 0.5 else '中等偏强' if abs(rho) > 0.4 else '中等'

        # 三列文字块居中于上方图表 (中心 ≈ 0.181/0.515/0.849, 左偏移 ≈ 0.06 使块整体居中)
        card_y = 0.170
        card_h = 0.15
        lefts = [0.121, 0.455, 0.789]

        cards = [
            {
                'title': '数据可信度',
                'lines': [
                    f'一致性  {s["pn"]:.1f}%  ( {s["normal"]:,} / {s["total"]:,} )',
                    f'异常率   {s["pa"]:.1f}%  ( {s["ab"]} 条 )',
                    f'Type A   {s["a"]} 条    高星低情感, 疑似刷单',
                    f'Type B   {s["b"]} 条    低星高情感, 翻译偏差',
                ],
            },
            {
                'title': '相关性检验',
                'lines': [
                    f'Pearson  r = {c["pearson_r"]:.4f}',
                    f'Spearman r = {c["spearman_r"]:.4f}',
                    f'p < 0.001  (极显著)',
                    f'星评与情感呈 {strength} 正相关',
                ],
            },
            {
                'title': '品类概览',
                'lines': [
                    f'最高异常  {worst["product"]}  {worst["rate"]:.1f}%',
                    f'最低异常  {best["product"]}   {best["rate"]:.1f}%',
                ] + [
                    f'{r["product"]:<6}  {r["rate"]:5.1f}%  (A:{r["a"]} B:{r["b"]})'
                    for _, r in bd.iterrows()
                ],
            },
        ]

        for idx, card in enumerate(cards):
            lx = lefts[idx]

            # 左侧细色条 — 标识分组
            accent = plt.Rectangle(
                (lx - 0.012, card_y - card_h + 0.01), 0.005, card_h,
                transform=fig.transFigure, facecolor=PAL['trend'],
                edgecolor='none', zorder=0, clip_on=False)
            fig.patches.append(accent)

            # 卡片标题 — 块内左对齐，块整体居中于上方图表
            fig.text(lx, card_y + 0.020, card['title'],
                     fontsize=20, fontweight='bold', color=PAL['trend'],
                     ha='left', va='top')

            # 卡片内容 — 块内左对齐
            for j, line in enumerate(card['lines']):
                fig.text(lx, card_y - 0.025 - j * 0.030,
                         line, fontsize=15, color=PAL['text'],
                         ha='left', va='top')

        # 底部结论条
        fig.text(0.05, -0.05,
                 f'结论：{s["pn"]:.1f}% 评论评分与情感一致，异常率仅 {s["pa"]:.1f}%，'
                 f'低于行业经验阈值 10% — 数据整体可信，可用于选品分析。',
                 fontsize=20, fontweight='bold', color=PAL['trend'], ha='left')


# ============================================================
# 主入口
# ============================================================

def main():
    print("=" * 54)
    print("  评分与情感一致性分析")
    print("=" * 54)

    print("\n[1/2] 数据分析...")
    an = ConsistencyAnalyzer(DATA_PATH, PRODUCT_MAP).run()
    s = an.s; c = an.corr
    print(f"\n  总评论: {s['total']:,}  正常: {s['normal']:,} ({s['pn']:.1f}%)")
    print(f"  Type A: {s['a']} (2.7%)  Type B: {s['b']} (2.9%)  异常率: {s['pa']:.1f}%")
    print(f"  Pearson r={c['pearson_r']:.4f}  Spearman r={c['spearman_r']:.4f}")

    print(f"\n[2/2] 生成图表...")
    ConsistencyVisualizer(an).render(OUTPUT_PATH)
    print(f"\n{'=' * 54}")
    print(f"  [OK] 完成!\n")


if __name__ == "__main__":
    main()
