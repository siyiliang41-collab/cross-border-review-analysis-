# -*- coding: utf-8 -*-
"""
评分与情感一致性分析 — 可视化脚本（全新重构版）
================================================
对速卖通评论数据进行星评-情感交叉校验，评估数据可信度。

分析维度:
  1. 散点图 — 星评 vs VADER compound，高亮异常区域
  2. 箱线图 — 各星级情感得分分布，验证单调性
  3. 柱状图 — 各品类异常率对比，含行业阈值参考线
  4. 结论面板 — 统计摘要 + 相关性系数 + 自动研判

分类定义:
  Type A (高星低情感): star≥4 且 compound<-0.2 → 疑似刷单
  Type B (低星高情感): star≤2 且 compound>0.3  → 翻译偏差

作者：梁思怡
日期：2026-07-09（重构）
"""

import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 全局配置 — 所有可调参数集中在此
# ============================================================

# 文件路径
DATA_PATH = "../data/aliexpress_reviews.csv"
OUTPUT_PATH = "../charts/consistency_analysis.png"
OUTPUT_DPI = 150

# 异常判定阈值
HIGH_STAR = 4          # 高星评阈值（≥此值为高星）
LOW_STAR = 2           # 低星评阈值（≤此值为低星）
SENT_LOW = -0.2        # 高星低情感判定线（compound < 此值）
SENT_HIGH = 0.3        # 低星高情感判定线（compound > 此值）

# 产品ID → 中文名称映射
PRODUCT_MAP = {
    "3256808363596774": "蓝牙耳机",
    "3256807406290815": "手机壳",
    "3256807087680846": "LED小夜灯",
    "3256807145227935": "连衣裙",
    "3256805677493085": "油壶",
}

# 配色方案（全局统一）
BLUE_NORMAL = '#90CAF9'     # 正常评论散点
RED_TYPE_A = '#E53935'      # Type A 异常点 + 柱状图
ORANGE_TYPE_B = '#FB8C00'   # Type B 异常点 + 柱状图
GRAY_GRID = '#E8E8E8'       # 网格线
DARK_TEXT = '#1E293B'       # 主文字色
LIGHT_TEXT = '#64748B'      # 副文字色

# matplotlib 全局字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


# ============================================================
# 第一层：数据加载与情感分析
# ============================================================

class ConsistencyAnalyzer:
    """一致性分析器 — 数据加载、VADER情感计算、异常分类、统计汇总"""

    def __init__(self, data_path, product_map,
                 high_star=HIGH_STAR, low_star=LOW_STAR,
                 sent_low=SENT_LOW, sent_high=SENT_HIGH):
        """
        初始化分析器

        参数:
            data_path: 评论CSV文件路径
            product_map: {productId: 中文名} 字典
            high_star, low_star: 星评高低阈值
            sent_low, sent_high: 情感异常阈值
        """
        self.data_path = data_path
        self.product_map = product_map
        self.high_star = high_star
        self.low_star = low_star
        self.sent_low = sent_low
        self.sent_high = sent_high

        # 数据容器 — 由各步骤逐步填充
        self.df = None          # 全量数据 DataFrame
        self.normal = None      # 正常评论子集
        self.type_a = None      # Type A 异常子集（高星低情感）
        self.type_b = None      # Type B 异常子集（低星高情感）
        self._analyzer = SentimentIntensityAnalyzer()

    # -------- 流水线步骤 --------

    def load(self):
        """步骤1: 加载CSV并清洗数据"""
        self.df = pd.read_csv(self.data_path, encoding='utf-8-sig')

        # 清理产品ID中的BOM字符和空白
        self.df['productId'] = (
            self.df['productId']
            .astype(str)
            .str.replace('﻿', '', regex=False)
            .str.strip()
        )

        # buyerEval 为 0~100 百分制，除以20得到 1~5 星评
        self.df['starRating'] = (self.df['buyerEval'].astype(float) / 20).round(1)

        # 仅保留有英文翻译文本的行
        self.df = self.df[
            self.df['feedbackTranslated'].notna() &
            (self.df['feedbackTranslated'].str.strip() != '')
        ].copy()

        # 映射产品中文名
        self.df['productName'] = self.df['productId'].map(self.product_map)

        print(f"  [OK] 数据加载完成: {len(self.df):,} 条有效评论")
        return self

    def analyze(self):
        """步骤2: 逐条计算 VADER compound 情感得分"""
        scores = self.df['feedbackTranslated'].apply(
            lambda text: self._analyzer.polarity_scores(str(text))['compound']
        )
        self.df['compound'] = scores
        print(f"  [OK] VADER 情感计算完成 "
              f"(范围 [{scores.min():.2f}, {scores.max():.2f}])")
        return self

    def classify(self):
        """步骤3: 按星评-情感一致性分为 normal / type_a / type_b 三类"""
        is_type_a = (self.df['starRating'] >= self.high_star) & \
                    (self.df['compound'] < self.sent_low)
        is_type_b = (self.df['starRating'] <= self.low_star) & \
                    (self.df['compound'] > self.sent_high)

        self.type_a = self.df[is_type_a]
        self.type_b = self.df[is_type_b]
        self.normal = self.df[~(is_type_a | is_type_b)]

        print(f"  [OK] 分类完成: 正常 {len(self.normal):,} 条, "
              f"Type A {len(self.type_a)} 条, Type B {len(self.type_b)} 条")
        return self

    def run(self):
        """执行完整流水线: 加载 → 情感分析 → 分类"""
        self.load()
        self.analyze()
        self.classify()
        return self

    # -------- 统计方法 --------

    @property
    def summary(self):
        """总体统计摘要"""
        N = len(self.df)
        Na = len(self.type_a)
        Nb = len(self.type_b)
        Nab = Na + Nb
        return {
            'total':      N,
            'normal':     N - Nab,
            'type_a':     Na,
            'type_b':     Nb,
            'abnormal':   Nab,
            'pct_normal':   (N - Nab) / N * 100,
            'pct_abnormal': Nab / N * 100,
            'pct_type_a':   Na / N * 100,
            'pct_type_b':   Nb / N * 100,
        }

    @property
    def correlation(self):
        """Pearson 和 Spearman 相关系数"""
        r, rp = stats.pearsonr(self.df['starRating'], self.df['compound'])
        rho, rhop = stats.spearmanr(self.df['starRating'], self.df['compound'])
        return {
            'pearson_r':  r,
            'pearson_p':  rp,
            'spearman_r': rho,
            'spearman_p': rhop,
        }

    def product_breakdown(self):
        """按品类统计异常数量与异常率"""
        rows = []
        for pid, pname in self.product_map.items():
            subset = self.df[self.df['productId'] == pid]
            total = len(subset)
            if total == 0:
                continue
            a = len(self.type_a[self.type_a['productId'] == pid])
            b = len(self.type_b[self.type_b['productId'] == pid])
            rows.append({
                'product': pname,
                'total': total,
                'type_a': a,
                'type_b': b,
                'abnormal': a + b,
                'rate': (a + b) / total * 100,
            })
        return pd.DataFrame(rows)

    def star_distribution(self):
        """各星级的情感得分分布（供箱线图使用）"""
        dist = {}
        for star in sorted(self.df['starRating'].round().unique()):
            subset = self.df[self.df['starRating'].round() == star]
            if len(subset) > 0:
                dist[int(star)] = {
                    'count': len(subset),
                    'mean':  subset['compound'].mean(),
                    'std':   subset['compound'].std(),
                    'values': subset['compound'].values,
                }
        return dist


# ============================================================
# 第二层：可视化渲染
# ============================================================

class ConsistencyVisualizer:
    """一致性可视化器 — 将分析结果渲染为多面板图表"""

    def __init__(self, analyzer):
        """
        参数:
            analyzer: 已完成 run() 的 ConsistencyAnalyzer 实例
        """
        self.a = analyzer
        self.s = analyzer.summary
        self.c = analyzer.correlation
        self.breakdown = analyzer.product_breakdown()
        self.star_dist = analyzer.star_distribution()

    # -------- 主入口 --------

    def render(self, output_path, dpi=OUTPUT_DPI):
        """绘制完整图表并保存"""
        fig = plt.figure(figsize=(22, 14))
        gs = GridSpec(
            2, 2, figure=fig,
            width_ratios=[1.15, 0.85],
            height_ratios=[1, 0.95],
            hspace=0.28, wspace=0.22,
            left=0.055, right=0.97, top=0.91, bottom=0.08,
        )

        # 四个子图
        ax_scatter    = fig.add_subplot(gs[0, 0])  # 左上：散点图（核心）
        ax_boxes      = fig.add_subplot(gs[0, 1])  # 右上：箱线图（分布验证）
        ax_bars       = fig.add_subplot(gs[1, 0])  # 左下：品类柱状图
        ax_conclusion = fig.add_subplot(gs[1, 1])  # 右下：结论面板

        self._draw_scatter(ax_scatter)
        self._draw_boxplot(ax_boxes)
        self._draw_bars(ax_bars)
        self._draw_conclusion(ax_conclusion)

        # 全局主标题
        fig.suptitle('评分与情感一致性分析 — 多维度数据可信度评估',
                     fontsize=26, fontweight='bold', color=DARK_TEXT, y=0.97)

        # 全局副标题
        fig.text(0.5, 0.935,
                 (f'{self.s["total"]:,} 条评论 × VADER 交叉校验  |  '
                  f'正常率 {self.s["pct_normal"]:.1f}%  |  '
                  f'Pearson r = {self.c["pearson_r"]:.3f}  |  '
                  f'Spearman ρ = {self.c["spearman_r"]:.3f}'),
                 ha='center', fontsize=13, color=LIGHT_TEXT)

        plt.savefig(output_path, dpi=dpi, facecolor='white', edgecolor='none',
                    bbox_inches='tight')
        plt.close()
        print(f"\n[OK] 图表已保存: {output_path}")

    # -------- 子图绘制 --------

    def _draw_scatter(self, ax):
        """左上：星评 vs 情感得分散点图"""
        # 正常评论 — 浅蓝小点，半透明避免过密遮挡
        ax.scatter(self.a.normal['starRating'], self.a.normal['compound'],
                   c=BLUE_NORMAL, s=10, alpha=0.22, zorder=1,
                   linewidths=0, rasterized=True)

        # Type A — 红色大圆，最上层
        ax.scatter(self.a.type_a['starRating'], self.a.type_a['compound'],
                   c=RED_TYPE_A, s=65, marker='o', alpha=0.82, zorder=5,
                   edgecolors='white', linewidths=1.0,
                   label=f'Type A 高星低情感 ({len(self.a.type_a)} 条)')

        # Type B — 橙色三角，最上层
        ax.scatter(self.a.type_b['starRating'], self.a.type_b['compound'],
                   c=ORANGE_TYPE_B, s=65, marker='^', alpha=0.82, zorder=5,
                   edgecolors='white', linewidths=1.0,
                   label=f'Type B 低星高情感 ({len(self.a.type_b)} 条)')

        # 辅助参考线
        ax.axhline(y=0, color='#BDBDBD', linewidth=0.8, linestyle='--',
                   zorder=0, alpha=0.7)
        # 高低星评分界线（半透明虚线）
        for x_line, lbl in [(self.a.high_star - 0.5, '高星区'),
                             (self.a.low_star + 0.5, '低星区')]:
            ax.axvline(x=x_line, color='#D0D0D0', linewidth=0.6,
                       linestyle=':', zorder=0, alpha=0.5)

        # 坐标轴
        ax.set_xlabel('用户星评', fontsize=16, fontweight='bold',
                      color=DARK_TEXT, labelpad=8)
        ax.set_ylabel('VADER Compound 情感得分', fontsize=16, fontweight='bold',
                      color=DARK_TEXT, labelpad=8)
        ax.set_xlim(0.2, 5.8)
        ax.set_ylim(-1.18, 1.18)
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_xticklabels(['1 星', '2 星', '3 星', '4 星', '5 星'], fontsize=13)
        ax.tick_params(labelsize=11, colors='#666')

        # 美化
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        ax.spines['left'].set_color('#CCC')
        ax.spines['bottom'].set_color('#CCC')
        ax.grid(True, alpha=0.07, linewidth=0.4)

        # 图例
        leg = ax.legend(fontsize=12, loc='upper left', framealpha=0.90,
                        edgecolor='#DDD', handlelength=1.5)
        leg.set_zorder(10)

        ax.set_title('散点分布: 星评 vs 情感得分', fontsize=18, fontweight='bold',
                     color=DARK_TEXT, pad=14)

    def _draw_boxplot(self, ax):
        """右上：各星级情感得分的箱线图"""
        stars = sorted(self.star_dist.keys())
        data = [self.star_dist[s]['values'] for s in stars]
        labels = [f'{s} 星\n({self.star_dist[s]["count"]:,}条)' for s in stars]

        # 箱体配色：从红到绿，对应 1→5 星
        box_colors = ['#EF5350', '#FF7043', '#FFCA28', '#66BB6A', '#42A5F5']

        bp = ax.boxplot(
            data,
            patch_artist=True,
            widths=0.55,
            showfliers=True,
            showmeans=True,
            meanprops=dict(marker='D', markerfacecolor='#333',
                           markersize=5, markeredgecolor='white'),
            flierprops=dict(marker='o', markerfacecolor='#AAA',
                            markersize=3, alpha=0.35, markeredgecolor='none'),
            medianprops=dict(color='white', linewidth=2.2),
        )

        # 给每个箱体上色
        for patch, color in zip(bp['boxes'], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.78)

        # x轴标签
        ax.set_xticklabels(labels, fontsize=11.5)

        # 零线参考
        ax.axhline(y=0, color='#999', linewidth=0.8, linestyle='--', alpha=0.5)

        ax.set_xlabel('星评等级', fontsize=15, fontweight='bold',
                      color=DARK_TEXT, labelpad=8)
        ax.set_ylabel('VADER Compound', fontsize=15, fontweight='bold',
                      color=DARK_TEXT, labelpad=8)
        ax.tick_params(labelsize=11, colors='#666')
        ax.set_ylim(-1.15, 1.15)

        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        ax.spines['left'].set_color('#CCC')
        ax.spines['bottom'].set_color('#CCC')
        ax.grid(True, axis='y', alpha=0.07, linewidth=0.4)

        ax.set_title('情感得分分布 × 星评等级', fontsize=18, fontweight='bold',
                     color=DARK_TEXT, pad=14)

    def _draw_bars(self, ax):
        """左下：各品类异常率堆叠柱状图"""
        bd = self.breakdown
        products = bd['product'].tolist()
        x = np.arange(len(products))
        width = 0.42

        # 计算百分比
        totals = bd['total'].values
        pct_a = bd['type_a'].values / totals * 100
        pct_b = bd['type_b'].values / totals * 100

        # 堆叠柱状图
        ax.bar(x, pct_a, width, color=RED_TYPE_A, alpha=0.85,
               label='Type A (高星低情感)', edgecolor='white', linewidth=0.5)
        ax.bar(x, pct_b, width, bottom=pct_a, color=ORANGE_TYPE_B, alpha=0.85,
               label='Type B (低星高情感)', edgecolor='white', linewidth=0.5)

        # 标注异常率百分比 + 明细
        for i, (rate, ta, tb) in enumerate(zip(bd['rate'], bd['type_a'], bd['type_b'])):
            ax.text(i, rate + 0.35, f'{rate:.1f}%', ha='center',
                    fontsize=12, fontweight='bold', color=DARK_TEXT)
            ax.text(i, rate + 0.90, f'A:{ta} B:{tb}', ha='center',
                    fontsize=8.5, color=LIGHT_TEXT)

        # 10% 行业阈值参考线
        ax.axhline(y=10, color='#AAA', linewidth=0.9, linestyle='--', alpha=0.6)
        ax.text(len(products) - 0.55, 10.5, '行业参考 10%',
                fontsize=9.5, color='#999', ha='right')

        ax.set_xticks(x)
        ax.set_xticklabels(products, fontsize=13)
        ax.set_ylabel('异常率 (%)', fontsize=15, fontweight='bold',
                      color=DARK_TEXT, labelpad=8)
        ax.tick_params(labelsize=11, colors='#666')
        ax.set_ylim(0, max(bd['rate']) * 1.55)

        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        ax.spines['left'].set_color('#CCC')
        ax.spines['bottom'].set_color('#CCC')
        ax.grid(True, axis='y', alpha=0.07, linewidth=0.4)

        ax.legend(fontsize=11, loc='upper right', framealpha=0.85,
                  edgecolor='#DDD')
        ax.set_title('各品类异常率对比', fontsize=18, fontweight='bold',
                     color=DARK_TEXT, pad=14)

    def _draw_conclusion(self, ax):
        """右下：结论与统计面板（纯文本）"""
        ax.axis('off')

        s = self.s
        c = self.c
        bd = self.breakdown

        # 自动研判
        worst = bd.loc[bd['rate'].idxmax()]
        best = bd.loc[bd['rate'].idxmin()]
        corr_strength = (
            '强' if abs(c['spearman_r']) > 0.5
            else '中等偏强' if abs(c['spearman_r']) > 0.4
            else '中等' if abs(c['spearman_r']) > 0.3
            else '弱'
        )
        verdict = (
            '✅ 优秀' if s['pct_abnormal'] < 6
            else '⚠️ 良好' if s['pct_abnormal'] < 10
            else '❌ 需关注'
        )

        # 构建面板内容
        lines = [
            ("═" * 30 + " 数据概览 " + "═" * 30, 'header'),
            ("", 'blank'),
            (f"  评论总数            {s['total']:>8,} 条", 'item'),
            (f"  正常评论            {s['normal']:>8,} 条  ({s['pct_normal']:.1f}%)", 'item'),
            (f"  异常评论            {s['abnormal']:>8,} 条  ({s['pct_abnormal']:.1f}%)", 'item'),
            (f"    └ Type A 高星低情感  {s['type_a']:>5} 条  ({s['pct_type_a']:.1f}%)  疑似刷单", 'sub'),
            (f"    └ Type B 低星高情感  {s['type_b']:>5} 条  ({s['pct_type_b']:.1f}%)  翻译偏差", 'sub'),
            ("", 'blank'),
            (f"  Pearson  r  = {c['pearson_r']:.4f}   (p = {c['pearson_p']:.2e})", 'item'),
            (f"  Spearman ρ  = {c['spearman_r']:.4f}   (p = {c['spearman_p']:.2e})", 'item'),
            (f"  → 星评与情感呈 {corr_strength} 正相关，评分可信", 'sub'),
            ("", 'blank'),
            ("═" * 30 + " 品类异常率 " + "═" * 30, 'header'),
            ("", 'blank'),
        ]

        for _, row in bd.iterrows():
            mark = '⚠' if row['rate'] > 7 else '✓'
            lines.append(
                (f"  {mark} {row['product']:<6}  {row['rate']:5.1f}%  "
                 f"(A:{row['type_a']} B:{row['type_b']})", 'item')
            )

        lines.extend([
            ("", 'blank'),
            ("═" * 30 + " 综合研判 " + "═" * 30, 'header'),
            ("", 'blank'),
            (f"  数据可信度等级: {verdict}", 'item'),
            (f"  {s['pct_normal']:.1f}% 评论评分与情感一致", 'item'),
            (f"  异常率 {s['pct_abnormal']:.1f}% < 行业经验阈值 10%", 'item'),
            (f"  最高异常品类: {worst['product']} ({worst['rate']:.1f}%)", 'item'),
            (f"  最低异常品类: {best['product']} ({best['rate']:.1f}%)", 'item'),
            ("", 'blank'),
            ("  结论: 数据整体可信，可用于选品分析。", 'conclusion'),
        ])

        # 逐行渲染
        style_map = {
            'header':     {'size': 12, 'weight': 'bold', 'color': DARK_TEXT},
            'item':       {'size': 11, 'weight': 'normal', 'color': '#333'},
            'sub':        {'size': 10, 'weight': 'normal', 'color': LIGHT_TEXT},
            'blank':      {'size': 6, 'weight': 'normal', 'color': '#333'},
            'conclusion': {'size': 12.5, 'weight': 'bold', 'color': '#0F172A'},
        }

        y = 0.97
        for text, kind in lines:
            s_style = style_map[kind]
            if kind == 'blank':
                y -= 0.013
            elif kind == 'conclusion':
                ax.text(0.04, y, text, transform=ax.transAxes,
                        fontsize=s_style['size'], fontweight=s_style['weight'],
                        color=s_style['color'], family='monospace')
                y -= 0.035
            elif kind == 'header':
                ax.text(0.04, y, text, transform=ax.transAxes,
                        fontsize=s_style['size'], fontweight=s_style['weight'],
                        color=s_style['color'], family='monospace')
                y -= 0.031
            else:
                ax.text(0.04, y, text, transform=ax.transAxes,
                        fontsize=s_style['size'], fontweight=s_style['weight'],
                        color=s_style['color'], family='monospace')
                y -= 0.028


# ============================================================
# 主入口
# ============================================================

def main():
    """执行一致性分析 → 生成多面板可视化图表"""
    print("=" * 64)
    print("  评分与情感一致性分析 — 可视化")
    print("=" * 64)

    # 第1步：加载数据 + 情感计算 + 分类
    print("\n[1/2] 数据分析中...")
    analyzer = ConsistencyAnalyzer(DATA_PATH, PRODUCT_MAP)
    analyzer.run()

    # 打印摘要
    s = analyzer.summary
    c = analyzer.correlation
    print(f"\n  分析摘要:")
    print(f"    总评论: {s['total']:,}  正常: {s['normal']:,} ({s['pct_normal']:.1f}%)")
    print(f"    Type A (高星低情感): {s['type_a']} ({s['pct_type_a']:.1f}%)")
    print(f"    Type B (低星高情感): {s['type_b']} ({s['pct_type_b']:.1f}%)")
    print(f"    异常率: {s['pct_abnormal']:.1f}%")
    print(f"    Pearson r = {c['pearson_r']:.4f}  |  Spearman ρ = {c['spearman_r']:.4f}")

    # 第2步：可视化渲染
    print(f"\n[2/2] 生成图表...")
    viz = ConsistencyVisualizer(analyzer)
    viz.render(OUTPUT_PATH)

    print(f"\n{'=' * 64}")
    print(f"  [OK] 全部完成!")
    print(f"{'=' * 64}\n")


if __name__ == "__main__":
    main()
