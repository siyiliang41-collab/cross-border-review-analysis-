# -*- coding: utf-8 -*-
"""
文件名：consistency_analysis.py
功能：评分与情感一致性分析 — 检测高星低情感（疑似刷单）和低星高情感（翻译偏差）
作者：梁思怡
创建日期：2026-07-09
"""
import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

print("=" * 60)
print("  评分与情感一致性分析 — 刷单嫌疑 + 翻译偏差检测")
print("=" * 60)

# ============================================================
# 1. 加载数据
# ============================================================
CSV_PATH = "../data/aliexpress_reviews.csv"
df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
df['productId'] = df['productId'].astype(str).str.replace('﻿', '').str.strip()
df['starRating'] = (df['buyerEval'].astype(float) / 20).round(1)  # 百分制→五分制

# 只看有英文翻译文本的评论
df = df[df['feedbackTranslated'].notna() & (df['feedbackTranslated'].str.strip() != '')]
print(f"\n[1/4] 有效评论: {len(df):,} 条（含英文评论文本）")

# ============================================================
# 2. VADER 情感打分（单例，避免重复实例化）
# ============================================================
analyzer = SentimentIntensityAnalyzer()
df['compound'] = df['feedbackTranslated'].apply(
    lambda t: analyzer.polarity_scores(str(t))['compound']
)
print(f"[2/4] VADER 打分完成, compound ∈ [{df['compound'].min():.2f}, {df['compound'].max():.2f}]")

# ============================================================
# 3. 异常检测
# ============================================================
# 类型A：高星低情感 — 星评≥4 但文本情绪为负 → 疑似刷单
high_star_low_sent = df[(df['starRating'] >= 4) & (df['compound'] < -0.2)]
# 类型B：低星高情感 — 星评≤2 但文本情绪为正 → 翻译偏差
low_star_high_sent = df[(df['starRating'] <= 2) & (df['compound'] > 0.3)]

n_a = len(high_star_low_sent)
n_b = len(low_star_high_sent)
total = len(df)
print(f"\n[3/4] 异常检测:")
print(f"  类型A「高星低情感」(star≥4, compound<-0.2): {n_a:>4} 条 ({n_a*100/total:.1f}%) → 疑似刷单")
print(f"  类型B「低星高情感」(star≤2, compound> 0.3):  {n_b:>4} 条 ({n_b*100/total:.1f}%) → 翻译偏差")
print(f"  合计异常: {n_a+n_b} 条, 异常率 {(n_a+n_b)*100/total:.2f}%")

# ============================================================
# 4. 各品类分布
# ============================================================
product_names = {
    "3256808363596774": "蓝牙耳机", "3256807406290815": "手机壳",
    "3256807087680846": "LED小夜灯", "3256807145227935": "连衣裙",
    "3256805677493085": "油壶",
}
print(f"\n[4/4] 各品类异常分布:")
print(f"  {'品类':<10} {'类型A':>6} {'类型B':>6} {'合计':>6} {'总评论':>6} {'异常率':>8}")
print(f"  {'-'*46}")
for pid, pname in product_names.items():
    a = len(high_star_low_sent[high_star_low_sent['productId'] == pid])
    b = len(low_star_high_sent[low_star_high_sent['productId'] == pid])
    t = len(df[df['productId'] == pid])
    r = 100*(a+b)/t if t > 0 else 0
    print(f"  {pname:<10} {a:>6} {b:>6} {a+b:>6} {t:>6} {r:>7.1f}%")

# 典型样本
print(f"\n--- 类型A 典型样本（高星低情感） ---")
for _, row in high_star_low_sent.sort_values('compound').head(5).iterrows():
    pname = product_names.get(row['productId'], row['productId'])
    print(f"  [{pname}] ★{row['starRating']} | compound={row['compound']:.2f} | {str(row['feedbackTranslated'])[:100]}")

print(f"\n--- 类型B 典型样本（低星高情感） ---")
for _, row in low_star_high_sent.sort_values('compound', ascending=False).head(5).iterrows():
    pname = product_names.get(row['productId'], row['productId'])
    print(f"  [{pname}] ★{row['starRating']} | compound={row['compound']:.2f} | {str(row['feedbackTranslated'])[:100]}")

print(f"\n{'=' * 60}")
print(f"  分析结论:")
print(f"  1. 仅 {n_a+n_b} 条存在评分-情感不一致（{100*(n_a+n_b)/total:.1f}%），数据整体可靠")
print(f"  2. 类型A {n_a} 条：高星但负面情感，可能是差评给了高分或无意义文本")
print(f"  3. 类型B {n_b} 条：低星但正面情感，VADER 对非英语表达的翻译文本有语义损耗")
print(f"  4. 正常率 {100-(n_a+n_b)*100/total:.1f}%，证明评论数据可用于后续分析")
print(f"{'=' * 60}")
