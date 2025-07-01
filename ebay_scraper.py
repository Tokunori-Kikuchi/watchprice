from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import json
import re
import time
import os
import random

# --- 定数定義 ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE_EBAY = os.path.join(SCRIPT_DIR, "ebay_cookies.json")
STEALTH_JS_PATH = os.path.join(SCRIPT_DIR, 'stealth.min.js')
# --- ▼▼▼ 未定義だった定数を追加 ▼▼▼ ---
USER_DATA_DIR = os.path.join(SCRIPT_DIR, "ebay_browser_profile")

# --- 優先ブランドリスト ---
PRIORITY_BRANDS = [
    "ロレックス", "ROLEX",
    "チューダー", "チュードル", "TUDOR",
    "オメガ", "OMEGA",
    "パテックフィリップ", "PATEK PHILIPPE",
    "オーデマピゲ", "AUDEMARS PIGUET",
    "グランドセイコー", "GRAND SEIKO",
    "カルティエ", "CARTIER",
    "パネライ", "PANERAI",
    "アイダブリューシー", "IWC",
    "ヴァシュロン・コンスタンタン", "VACHERON CONSTANTIN"
]

def save_cookies(context, path):
    try:
        with open(path, 'w') as f:
            json.dump(context.cookies(), f)
        print(f"クッキーを {path} に保存しました。")
    except Exception as e:
        print(f"クッキーの保存中にエラーが発生しました: {e}")

def load_cookies(context, path):
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                cookies = json.load(f)
                context.add_cookies(cookies)
            print(f"{path} からクッキーを読み込みました。")
            return True
        except Exception as e:
            print(f"クッキーの読み込み中にエラーが発生しました: {e}")
    return False

def human_like_delay(min_sec=1.5, max_sec=4.0):
    time.sleep(random.uniform(min_sec, max_sec))

def parse_ebay_page(soup):
    products = []
    items = soup.select('li.s-item')
    for item in items:
        if item.select_one('.s-item__title--tagblock, .s-item__title--tag'):
            continue
        name_tag = item.select_one('h3.s-item__title, div.s-item__title > span')
        price_tag = item.select_one('span.s-item__price')
        url_tag = item.select_one('a.s-item__link')
        image_tag = item.select_one('div.s-item__image-wrapper img')
        if not all([name_tag, price_tag, url_tag, image_tag]):
            continue
        name = name_tag.get_text(strip=True)
        url = url_tag['href']
        image_url = image_tag.get('src')
        price_text = price_tag.get_text(strip=True).replace('￥', '').replace(',', '').replace('円', '')
        price_match = re.search(r'[\d.]+', price_text)
        price = int(float(price_match.group())) if price_match else 0
        if price == 0:
            continue
        products.append({
            'name': name, 'price': price, 'url': url,
            'image_url': image_url, 'site_name': 'eBay'
        })
    return products

def calc_json_bytes(data):
    return len(json.dumps(data, ensure_ascii=False).encode('utf-8'))

def scrape_ebay(search_query="rolex submariner", max_pages=2):
    all_products = []
    if not os.path.exists(STEALTH_JS_PATH):
        print(f"エラー: stealth.min.js が見つかりません。")
        return None

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=True,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            locale='ja-JP',
            viewport={'width': 1920, 'height': 1080},
            slow_mo=50
        )

        page = context.new_page()
        page.add_init_script(path=STEALTH_JS_PATH)

        try:
            # 2回目以降の実行のために、まずクッキーを読み込む
            load_cookies(context, COOKIE_FILE_EBAY)

            pages_to_scrape = max_pages if max_pages != 0 else 2
            for page_num in range(1, pages_to_scrape + 1):
                url = f"https://www.ebay.com/sch/i.html?_from=R40&_nkw={search_query.replace(' ', '+')}&_sacat=0&LH_PrefLoc=5&_fsrp=1&rt=nc&LH_FS=1&_ipg=240&_pgn={page_num}"
                print(f"eBay: {page_num}ページ目を取得中...")
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                page.wait_for_selector('ul.srp-results li.s-item', timeout=30000)
                human_like_delay()

                html_content = page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                products_on_page = parse_ebay_page(soup)

                if not products_on_page and page_num > 1:
                    print("eBay: これ以上商品が見つかりませんでした。")
                    break
                all_products.extend(products_on_page)

            save_cookies(context, COOKIE_FILE_EBAY)
            context.close()
            return all_products
        except Exception as e:
            print(f"eBayのスクレイピング中にエラーが発生しました: {e}")
            page.screenshot(path='ebay_error_screenshot.png')
            context.close()
            return None

def scrape_ebay_priority_brands(max_pages=2, max_total_bytes=4_500_000_000, already_bytes=0):
    all_products = []
    total_bytes = already_bytes
    for brand in PRIORITY_BRANDS:
        if total_bytes >= max_total_bytes:
            print("容量上限に達したためeBayの取得を停止します。")
            break
        print(f"\n--- eBayブランド検索: {brand} ---")
        products = scrape_ebay(search_query=brand, max_pages=max_pages)
        if products:
            all_products.extend(products)
            total_bytes += calc_json_bytes(products)
            print(f"eBay: {brand} で {len(products)}件取得、累計 {total_bytes/1_000_000:.2f}MB")
    return all_products

def main():
    """このスクリプトを単体で実行するためのメイン関数"""
    print("--- eBayの単体スクレイピングを開始します ---")
    scraped_products = scrape_ebay(max_pages=1)
    if scraped_products:
        output_filename = "ebay_scraped_data.json"
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(scraped_products, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 合計{len(scraped_products)}件のデータを '{output_filename}' に正常に出力しました。")
        except Exception as e:
            print(f"\n❌ ファイル出力中にエラーが発生しました: {e}")
    else:
        print("商品情報の取得に失敗しました。")

if __name__ == "__main__":
    main()