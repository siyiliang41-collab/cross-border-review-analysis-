# -*- coding: utf-8 -*-
"""
速卖通评论爬虫 - 完整可用版

用法：
  1. 把商品ID填入下方 PRODUCT_IDS 列表
  2. 从浏览器复制 _m_h5_tk 的值填入 MANUAL_COOKIE_M_H5_TK
  3. 运行 python aliexpress_scraper.py
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
# 配置区 - 按需修改
# ============================================================

# 商品ID列表 - 从商品页URL中提取
PRODUCT_IDS = [
    "3256808363596774",
    "3256807406290815",
    "3256807087680846",
    "3256807145227935",
    "3256805677493085",
    

    

    
]

# 从浏览器复制 _m_h5_tk 的值
# 操作：F12 -> Application -> Cookies -> aliexpress.com -> 搜索 _m_h5_tk -> 复制整段
MANUAL_COOKIE_M_H5_TK = "c7f8526f4f2f77f096280b661ffdf9d8_1783321038066"

# 每个商品最多爬取页数，0表示不限制（采集全量）
MAX_PAGES_PER_PRODUCT = 0
PAGE_SIZE = 20

# 代理设置，直连无需代理时把 USE_PROXY 改为 False
PROXY = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}
USE_PROXY = True

OUTPUT_FILE = "aliexpress_reviews.csv"

# ============================================================
# 核心类 - 无需修改
# ============================================================

class AliExpressReviewScraper:
    """速卖通评论采集器"""

    # 速卖通 Web 端公开 appKey，固定值
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

    # ------------------------------------------------------------------
    # Token 与签名
    # ------------------------------------------------------------------

    def _get_token(self):
        """获取 mtop 签名所需的 token
           优先使用手动配置的 _m_h5_tk，否则访问首页自动获取
        """
        if MANUAL_COOKIE_M_H5_TK:
            self.session.cookies.set(
                "_m_h5_tk", MANUAL_COOKIE_M_H5_TK, domain=".aliexpress.com"
            )
            return MANUAL_COOKIE_M_H5_TK.split("_")[0]

        print("[*] 访问速卖通首页获取 token ...")
        self.session.get(
            "https://www.aliexpress.com/", timeout=15, allow_redirects=True
        )
        cookie = self.session.cookies.get("_m_h5_tk")
        if cookie:
            token = cookie.split("_")[0]
            print(f"[+] Token 获取成功: {token[:16]}...")
            return token
        raise Exception(
            "无法自动获取 _m_h5_tk cookie，"
            "请从浏览器手动复制并填入 MANUAL_COOKIE_M_H5_TK"
        )

    def _cached_token(self):
        """从当前会话缓存中读取 token"""
        cookie = self.session.cookies.get("_m_h5_tk")
        if not cookie:
            raise Exception(
                "_m_h5_tk 已过期或丢失，请重新从浏览器复制"
            )
        return cookie.split("_")[0]

    def _sign(self, token, ts, data_str):
        """生成 mtop 签名：MD5(token & t & appKey & data_json)"""
        raw = f"{token}&{ts}&{self.APP_KEY}&{data_str}"
        return hashlib.md5(raw.encode()).hexdigest()

    # ------------------------------------------------------------------
    # 商品页解析
    # ------------------------------------------------------------------

    def _get_seller_seq(self, product_id):
        """从商品详情页 HTML 中提取 sellerAdminSeq"""
        print(f"[*] 获取商品 {product_id} 的卖家信息 ...")
        url = f"https://www.aliexpress.com/item/{product_id}.html"
        resp = self.session.get(url, timeout=15, allow_redirects=True)
        m = re.search(r'"sellerAdminSeq"\s*:\s*(\d+)', resp.text)
        if m:
            print(f"[+] sellerAdminSeq = {m.group(1)}")
            return m.group(1)
        print("[!] 未找到 sellerAdminSeq，使用默认值继续")
        return "2678280160"

    # ------------------------------------------------------------------
    # 评论 API 调用
    # ------------------------------------------------------------------

    def fetch_reviews(self, product_id, seller_seq, page=1):
        """调用速卖通 mtop 接口，返回单页评论数据"""
        # 构造请求体 JSON
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

        # 生成签名
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

        # 返回是 JSONP 格式：mtopjsonpX({...})，去掉外层函数包装
        text = resp.text.strip()  # 去首尾空白，服务器有时返回前导空格

        # 检测异常响应（HTML页面、空响应等）
        if not text or len(text) < 20:
            raise Exception(f"响应为空或过短，cookie可能已过期。重新从浏览器复制 _m_h5_tk")

        if text.startswith("<") or text.startswith("<!DOCTYPE"):
            raise Exception(f"返回了HTML页面（非JSON），cookie或签名验证失败。重新从浏览器复制 _m_h5_tk")

        # 去掉 JSONP 外层包装 mtopjsonpX( ... )
        idx = text.find("(")
        if idx > 0:
            text = text[idx + 1:-1]

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            raise Exception(
                f"JSON解析失败，服务器返回异常。"
                f"响应前200字符: {resp.text[:200]}"
            )

        ret = result.get("ret", [])
        if "SUCCESS" not in str(ret):
            raise Exception(f"API 返回错误: {ret}")

        return result.get("data", {})

    # ------------------------------------------------------------------
    # 单条评论解析
    # ------------------------------------------------------------------

    def parse_review(self, review):
        """将 API 返回的原始评论转为结构化字段"""
        return {
            "evaluationId": review.get("evaluationIdStr", ""),
            "buyerCountry": review.get("buyerCountry", ""),
            "buyerName": review.get("buyerName", ""),
            # 原始为百分制，转五分制便于分析
            "buyerEval": review.get("buyerEval", ""),
            "starRating": round(review.get("buyerEval", 0) / 20, 1),
            # 评论文本（原文 + 英文翻译版）
            "feedback": review.get("buyerFeedback", ""),
            "feedbackTranslated": review.get("buyerTranslationFeedback", ""),
            "evalDate": review.get("evalDate", ""),
            # 购买属性（颜色 / 尺码等）
            "skuInfo": review.get("skuInfo", ""),
            # 物流方式
            "logistics": review.get("logistics", ""),
            # 有用 / 无用 投票
            "upVoteCount": review.get("upVoteCount", 0),
            "downVoteCount": review.get("downVoteCount", 0),
            # 是否有图片、是否有追评
            "hasImage": 1 if review.get("images") else 0,
            "hasFollowUp": 1 if review.get("buyerAddFbContent") else 0,
            "addFeedback": review.get("buyerAddFbContent", ""),
            "anonymous": review.get("anonymous", False),
            # 平台提取的产品特征标签
            "label1": review.get("reviewLabel1", ""),
            "labelValue1": review.get("reviewLabelValue1", ""),
            "label2": review.get("reviewLabel2", ""),
            "labelValue2": review.get("reviewLabelValue2", ""),
            "label3": review.get("reviewLabel3", ""),
            "labelValue3": review.get("reviewLabelValue3", ""),
        }

    # ------------------------------------------------------------------
    # 单个商品全量采集
    # ------------------------------------------------------------------

    def scrape_product(self, product_id, writer):
        """爬取一个商品的全部评论，逐行写入 CSV"""
        self._get_token()
        seller_seq = self._get_seller_seq(product_id)

        print(f"\n{'=' * 60}")
        print(f"[*] 开始采集商品: {product_id}")
        print(f"{'=' * 60}")

        max_pages = MAX_PAGES_PER_PRODUCT
        page = 1
        count = 0
        retry_count = 0
        MAX_RETRY = 3  # 同一页最多重试次数

        while True:
            # 如果设置了页数上限且已达到，停止采集
            if MAX_PAGES_PER_PRODUCT > 0 and page > max_pages:
                break

            try:
                print(f"  [>] 第 {page} 页 ...", end=" ")
                data = self.fetch_reviews(product_id, seller_seq, page)

                # 首页打印统计概览，并根据真实总页数确定采集上限
                if page == 1:
                    total_page = data.get("totalPage", 1)
                    if MAX_PAGES_PER_PRODUCT > 0:
                        max_pages = min(total_page, MAX_PAGES_PER_PRODUCT)
                    else:
                        max_pages = total_page
                    stats = data.get("productEvaluationStatistic", {})
                    print(
                        f"\n  [i] 总评论: {data.get('totalNum', 0)} 条, "
                        f"均分: {stats.get('evarageStar', '?')}, "
                        f"总页数: {total_page}"
                    )
                    print(f"  [>] 第 {page} 页 ...", end=" ")

                reviews = data.get("evaViewList", [])
                for r in reviews:
                    row = self.parse_review(r)
                    row["productId"] = product_id
                    writer.writerow(row)
                    count += 1

                print(f"OK ({len(reviews)} 条)")

                if len(reviews) < PAGE_SIZE:
                    print("  [i] 已到最后一页")
                    break

                page += 1
                retry_count = 0  # 成功则重置重试计数
                # 随机延时 1.5~3.0 秒，降低被识别为爬虫的概率
                time.sleep(random.uniform(1.5, 3.0))

            except Exception as e:
                print(f"失败: {e}")
                retry_count += 1
                if retry_count > MAX_RETRY:
                    print(f"  [!] 已重试 {MAX_RETRY} 次仍然失败，跳过本商品剩余页面")
                    break
                wait = 5 * retry_count
                print(f"  [!] 等待 {wait} 秒后第 {retry_count}/{MAX_RETRY} 次重试 ...")
                time.sleep(wait)

        print(f"[+] 商品 {product_id} 采集完成，共 {count} 条评论")
        return count


# ============================================================
# 入口
# ============================================================

def main():
    print("=" * 60)
    print("  速卖通评论爬虫")
    print("=" * 60)

    scraper = AliExpressReviewScraper()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILE)

    # CSV 列定义
    fields = [
        "productId", "evaluationId", "buyerCountry", "buyerName",
        "buyerEval", "starRating", "feedback", "feedbackTranslated",
        "evalDate", "skuInfo", "logistics",
        "upVoteCount", "downVoteCount", "hasImage", "hasFollowUp",
        "addFeedback", "anonymous",
        "label1", "labelValue1", "label2", "labelValue2",
        "label3", "labelValue3",
    ]

    # 判断是否续爬：如果文件已存在且有内容，追加模式 + 跳过已完成的商品
    file_exists = os.path.exists(out) and os.path.getsize(out) > 200  # 200字节=header
    mode = "a" if file_exists else "w"

    # 如果文件已存在，读取已采集的商品ID，避免重复爬取
    done_products = set()
    if file_exists:
        with open(out, "r", encoding="utf-8-sig") as existing:
            reader = csv.DictReader(existing)
            for row in reader:
                done_products.add(row.get("productId", ""))
        print(f"[i] 检测到已有数据文件，已采集 {len(done_products)} 个商品，将跳过")

    with open(out, mode, newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not file_exists:
            writer.writeheader()
        total = sum(
            scraper.scrape_product(pid, writer) for pid in PRODUCT_IDS if pid not in done_products
        )

    print(f"\n{'=' * 60}")
    print(f"  全部完成！本次采集 {total} 条评论（不含续爬数据）")
    print(f"  输出文件: {out}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
