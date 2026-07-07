# -*- coding: utf-8 -*-
"""
速卖通评论爬虫 - 全量采集版 v3
==============================================
基于v1稳定版，仅添加：
  1. 页级断点续爬 — progress.json，Ctrl+C不丢进度
  2. 评价ID去重 — 连续3页全重复则API循环→自动停止

用法：
  1. 从浏览器复制 _m_h5_tk 的值填入 MANUAL_COOKIE_M_H5_TK
  2. 运行 python aliexpress_scraper.py
==============================================
"""

import requests
import hashlib
import time
import json
import csv
import os
import re
import random

# ============================================================
# 配置区
# ============================================================

PRODUCT_IDS = [
    "3256808363596774",  # 蓝牙耳机
    "3256807406290815",  # 手机壳
    "3256807087680846",  # LED小夜灯
    "3256807145227935",  # 女士连衣裙
    "3256805677493085",  # 厨房油壶
]

MANUAL_COOKIE_M_H5_TK = "d91a1a59e38766130e15c496603ef6ca_1783387947614"

MAX_PAGES_PER_PRODUCT = 0
PAGE_SIZE = 20

PROXY = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}
USE_PROXY = True

OUTPUT_FILE = "aliexpress_reviews.csv"
PROGRESS_FILE = "progress.json"

# ============================================================
# 核心类（与v1稳定版一致，仅添加去重逻辑）
# ============================================================

class AliExpressReviewScraper:
    APP_KEY = "12574478"
    BASE_URL = "https://acs.aliexpress.com/h5/mtop.aliexpress.review.pc.list/1.0/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/149.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.aliexpress.com/",
        })
        if USE_PROXY:
            self.session.proxies.update(PROXY)

    def _get_token(self):
        """获取签名token"""
        if MANUAL_COOKIE_M_H5_TK:
            self.session.cookies.set(
                "_m_h5_tk", MANUAL_COOKIE_M_H5_TK, domain=".aliexpress.com"
            )
            return MANUAL_COOKIE_M_H5_TK.split("_")[0]

        print("[*] 访问首页获取token...")
        self.session.get("https://www.aliexpress.com/", timeout=15, allow_redirects=True)
        cookie = self.session.cookies.get("_m_h5_tk")
        if cookie:
            print(f"[+] Token: {cookie[:16]}...")
            return cookie.split("_")[0]
        raise Exception("无法获取 _m_h5_tk，请手动填入配置")

    def _cached_token(self):
        """读session cookie中的token（与v1原始逻辑一致）"""
        cookie = self.session.cookies.get("_m_h5_tk")
        if not cookie:
            raise Exception("_m_h5_tk 已过期，请重新从浏览器复制")
        return cookie.split("_")[0]

    def _sign(self, token, ts, data_str):
        raw = f"{token}&{ts}&{self.APP_KEY}&{data_str}"
        return hashlib.md5(raw.encode()).hexdigest()

    def fetch_reviews(self, product_id, seller_seq, page=1):
        """调用API获取单页评论"""
        data_obj = {
            "productId": str(product_id),
            "page": page,
            "pageSize": PAGE_SIZE,
            "_lang": "en_US",
            "filter": "all",
            "sort": "complex_default",
            "country": "US",
            "sellerAdminSeq": int(seller_seq),
            "clientType": "web",
        }
        data_str = json.dumps(data_obj, separators=(",", ":"))
        ts = str(int(time.time() * 1000))
        token = self._cached_token()

        params = {
            "jsv": "2.7.2",
            "appKey": self.APP_KEY,
            "t": ts,
            "sign": self._sign(token, ts, data_str),
            "api": "mtop.aliexpress.review.pc.list",
            "v": "1.0",
            "type": "jsonp",
            "dataType": "jsonp",
            "callback": "mtopjsonp6",
            "data": data_str,
        }

        resp = self.session.get(self.BASE_URL, params=params, timeout=20)
        text = resp.text.strip()

        if not text or len(text) < 20:
            raise Exception("响应过短，cookie可能过期")
        if text.startswith("<"):
            raise Exception("返回HTML，cookie或签名验证失败")

        idx = text.find("(")
        if idx > 0:
            text = text[idx + 1:-1]

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            raise Exception(f"JSON解析失败: {resp.text[:200]}")

        ret = result.get("ret", [])
        if "SUCCESS" not in str(ret):
            raise Exception(f"API错误: {ret}")
        return result.get("data", {})

    def parse_review(self, review):
        return {
            "evaluationId": review.get("evaluationIdStr", ""),
            "buyerCountry": review.get("buyerCountry", ""),
            "buyerName": review.get("buyerName", ""),
            "buyerEval": review.get("buyerEval", ""),
            "starRating": round(review.get("buyerEval", 0) / 20, 1),
            "feedback": review.get("buyerFeedback", ""),
            "feedbackTranslated": review.get("buyerTranslationFeedback", ""),
            "evalDate": review.get("evalDate", ""),
            "skuInfo": review.get("skuInfo", ""),
            "logistics": review.get("logistics", ""),
            "upVoteCount": review.get("upVoteCount", 0),
            "downVoteCount": review.get("downVoteCount", 0),
            "hasImage": 1 if review.get("images") else 0,
            "hasFollowUp": 1 if review.get("buyerAddFbContent") else 0,
            "addFeedback": review.get("buyerAddFbContent", ""),
            "anonymous": review.get("anonymous", False),
            "label1": review.get("reviewLabel1", ""),
            "labelValue1": review.get("reviewLabelValue1", ""),
            "label2": review.get("reviewLabel2", ""),
            "labelValue2": review.get("reviewLabelValue2", ""),
            "label3": review.get("reviewLabel3", ""),
            "labelValue3": review.get("reviewLabelValue3", ""),
        }

    def scrape_product(self, product_id, writer):
        """采集一个商品的全部评论"""
        self._get_token()
        seller_seq = "2678280160"

        print(f"\n{'=' * 60}")
        print(f"[*] 开始采集: {product_id}")

        max_pages = MAX_PAGES_PER_PRODUCT
        page = 1
        count = 0
        retry_count = 0
        MAX_RETRY = 3

        # ===== v3新增：去重检测 =====
        seen_ids = set()
        dup_streak = 0
        MAX_DUP_STREAK = 3

        # ===== v3新增：页级断点 =====
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, "r", encoding="utf-8") as pf:
                progress = json.load(pf)
            if product_id in progress:
                page = progress[product_id] + 1
                print(f"  [i] 从第 {page} 页续爬")

        while True:
            if MAX_PAGES_PER_PRODUCT > 0 and page > max_pages:
                break

            try:
                print(f"  [>] 第 {page} 页 ...", end=" ", flush=True)
                data = self.fetch_reviews(product_id, seller_seq, page)

                # 首页打印统计
                if page == 1:
                    total_page = data.get("totalPage", 1)
                    if MAX_PAGES_PER_PRODUCT > 0:
                        max_pages = min(total_page, MAX_PAGES_PER_PRODUCT)
                    else:
                        max_pages = total_page
                    stats = data.get("productEvaluationStatistic", {})
                    print(f"\n  [i] 总评论: {data.get('totalNum', 0)} 条, "
                          f"均分: {stats.get('evarageStar', '?')}, "
                          f"总页数: {total_page}")
                    print(f"  [>] 第 {page} 页 ...", end=" ")

                reviews = data.get("evaViewList", [])

                # ===== v3新增：去重写入 =====
                new_count = 0
                for r in reviews:
                    eid = r.get("evaluationIdStr", "")
                    if eid and eid not in seen_ids:
                        seen_ids.add(eid)
                        row = self.parse_review(r)
                        row["productId"] = product_id
                        writer.writerow(row)
                        count += 1
                        new_count += 1

                if len(reviews) > 0 and new_count == 0:
                    dup_streak += 1
                    print(f"全重复({dup_streak}/{MAX_DUP_STREAK})", flush=True)
                    if dup_streak >= MAX_DUP_STREAK:
                        print("  [i] 连续3页全重复，API循环，停止")
                        break
                else:
                    dup_streak = 0
                    print(f"OK (+{new_count})", flush=True)

                # ===== v3新增：更新断点 =====
                with open(PROGRESS_FILE, "w", encoding="utf-8") as pf:
                    # 读取已有断点，合并写入
                    exist = {}
                    if os.path.exists(PROGRESS_FILE):
                        try:
                            with open(PROGRESS_FILE, "r", encoding="utf-8") as ef:
                                exist = json.load(ef)
                        except:
                            pass
                    exist[product_id] = page
                    json.dump(exist, pf)

                if len(reviews) < PAGE_SIZE:
                    print("  [i] 已到最后一页")
                    break

                page += 1
                retry_count = 0
                # 与原版一致的随机延时
                time.sleep(random.uniform(1.5, 3.0))

            except Exception as e:
                print(f"失败: {e}")
                retry_count += 1
                if retry_count > MAX_RETRY:
                    print(f"  [!] 重试{MAX_RETRY}次仍失败，跳过")
                    page += 1
                    retry_count = 0
                    continue
                wait = 5 * retry_count
                print(f"  [!] {wait}s后重试 ({retry_count}/{MAX_RETRY})")
                time.sleep(wait)

        # 采集完成，清断点
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, "r", encoding="utf-8") as pf:
                exist = json.load(pf)
            exist.pop(product_id, None)
            with open(PROGRESS_FILE, "w", encoding="utf-8") as pf:
                json.dump(exist, pf)

        print(f"[+] 商品 {product_id} 完成，共 {count} 条")
        return count


# ============================================================
# 入口
# ============================================================

def main():
    print("=" * 60)
    print("  速卖通评论爬虫 v3（v1稳定版 + 去重 + 页级断点）")
    print("=" * 60)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILE)
    fields = [
        "productId", "evaluationId", "buyerCountry", "buyerName",
        "buyerEval", "starRating", "feedback", "feedbackTranslated",
        "evalDate", "skuInfo", "logistics",
        "upVoteCount", "downVoteCount", "hasImage", "hasFollowUp",
        "addFeedback", "anonymous",
        "label1", "labelValue1", "label2", "labelValue2",
        "label3", "labelValue3",
    ]

    file_exists = os.path.exists(out) and os.path.getsize(out) > 200
    mode = "a" if file_exists else "w"

    done_products = set()
    if file_exists:
        with open(out, "r", encoding="utf-8-sig") as existing:
            reader = csv.DictReader(existing)
            for row in reader:
                done_products.add(row.get("productId", ""))
        print(f"[i] 已有 {len(done_products)} 个商品数据，跳过")

    pending = [p for p in PRODUCT_IDS if p not in done_products]
    if not pending:
        print("[i] 全部完成！")
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        return

    print(f"[i] 待采集: {len(pending)} 个商品")

    scraper = AliExpressReviewScraper()
    with open(out, mode, newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not file_exists:
            writer.writeheader()
        total = sum(scraper.scrape_product(pid, writer) for pid in pending)

    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    print(f"\n{'=' * 60}")
    print(f"  完成！本次采集 {total} 条 → {out}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
