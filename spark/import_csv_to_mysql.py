# -*- coding: utf-8 -*-
"""
文件名：import_csv_to_mysql.py
功能：将 aliexpress_reviews.csv 导入 MySQL bipt_review 表
用法：python import_csv_to_mysql.py
依赖：pip install pymysql pandas
作者：梁思怡  日期：2026-07-09
"""
import pandas as pd
import pymysql
import sys

# ============================================================
# 配置（按实际环境修改）
# ============================================================
DB_CONFIG = {
    "host": "192.168.229.101",
    "port": 3306,
    "user": "root",
    "password": "Root@123456",
    "database": "bipt_project",
    "charset": "utf8mb4",
}

CSV_PATH = "../data/aliexpress_reviews.csv"
BATCH_SIZE = 1000  # 每批插入行数

# CSV 列名 → MySQL 列名 映射
COLUMN_MAP = {
    "productId":          "product_id",
    "evaluationId":       "evaluation_id",
    "buyerCountry":       "buyer_country",
    "buyerName":          "buyer_name",
    "buyerEval":          "buyer_eval",
    "starRating":         "star_rating",
    "feedback":           "feedback",
    "feedbackTranslated": "feedback_translated",
    "evalDate":           "eval_date",
    "skuInfo":            "sku_info",
    "logistics":          "logistics",
    "upVoteCount":        "up_vote_count",
    "downVoteCount":      "down_vote_count",
    "hasImage":           "has_image",
    "hasFollowUp":        "has_follow_up",
    "addFeedback":        "add_feedback",
    "anonymous":          "anonymous",
    "label1":             "label1",
    "labelValue1":        "label_value1",
    "label2":             "label2",
    "labelValue2":        "label_value2",
    "label3":             "label3",
    "labelValue3":        "label_value3",
}

# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 60)
    print("  CSV → MySQL bipt_review 表 数据导入")
    print("=" * 60)

    # 1. 读取 CSV
    print("\n[1/4] 读取 CSV...")
    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
    df['productId'] = df['productId'].astype(str).str.replace('﻿', '').str.strip()
    # 处理空值
    df = df.where(pd.notnull(df), None)
    print(f"  CSV 行数: {len(df):,}")

    # 2. 连接 MySQL
    print("\n[2/4] 连接 MySQL...")
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 清空旧数据
    cursor.execute("TRUNCATE TABLE bipt_review")
    print("  旧数据已清空")

    # 3. 构建 INSERT SQL
    mysql_cols = list(COLUMN_MAP.values())
    placeholders = ", ".join(["%s"] * len(mysql_cols))
    sql = f"INSERT INTO bipt_review ({', '.join(mysql_cols)}) VALUES ({placeholders})"

    # 4. 批量插入
    print(f"\n[3/4] 开始批量插入（每批 {BATCH_SIZE} 行）...")
    total = len(df)
    inserted = 0
    csv_cols = list(COLUMN_MAP.keys())

    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch = []
        for _, row in df.iloc[start:end].iterrows():
            batch.append(tuple(row[col] for col in csv_cols))
        cursor.executemany(sql, batch)
        conn.commit()
        inserted += len(batch)
        pct = inserted * 100 / total
        print(f"  [{inserted:>6}/{total}] {pct:.1f}%", end='\r')

    print(f"\n  [OK] 全部 {inserted:,} 条导入完成")

    # 5. 验证
    print(f"\n[4/4] 验证...")
    cursor.execute("SELECT COUNT(*) FROM bipt_review")
    db_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT product_id) FROM bipt_review")
    db_products = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT buyer_country) FROM bipt_review")
    db_countries = cursor.fetchone()[0]
    print(f"  表记录数: {db_count:,}")
    print(f"  商品数: {db_products}  国家数: {db_countries}")

    cursor.close()
    conn.close()

    print(f"\n{'=' * 60}")
    print(f"  [OK] 导入完成！CRUD 模块数据已就绪")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
