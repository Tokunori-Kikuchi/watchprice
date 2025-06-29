from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import json
import re
import time
import math
import os
import random

# --- 定数とヘルパー関数 ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(SCRIPT_DIR, "chrono24_cookies.json")

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

def human_like_delay(min_sec=1.0, max_sec=3.0):
    time.sleep(random.uniform(min_sec, max_sec))

def parse_page_data(soup):
    try:
        json_ld_script = soup.find('script', type='application/ld+json')
        if not json_ld_script: return []
        data = json.loads(json_ld_script.string)
        offers_list = []
        graph_data = data.get('@graph', [])
        if not isinstance(graph_data, list): return []
        for item in graph_data:
            if isinstance(item, dict) and item.get('@type') == 'AggregateOffer':
                offers_list = item.get('offers', [])
                break
        products = []
        for offer in offers_list:
            if not isinstance(offer, dict): continue
            image_info = offer.get('image', {})
            products.append({
                'name': offer.get('name'),
                'price': offer.get('price'),
                'url': offer.get('url'),
                'image_url': image_info.get('contentUrl') if isinstance(image_info, dict) else None,
                'site_name': 'Chrono24' # サイト名を追加
            })
        return products
    except Exception as e:
        print(f"Chrono24のページデータ解析中にエラーが発生しました: {e}")
        return []

def scrape_chrono24_submariner(max_pages=2):
    all_products = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale='ja-JP'
        )
        load_cookies(context, COOKIE_FILE)
        page = context.new_page()
        base_url = "https://www.chrono24.jp/rolex/submariner--mod1.htm"
        try:
            print("Chrono24: 1ページ目を取得中...")
            page.goto(base_url, wait_until='domcontentloaded', timeout=60000)
            accept_button_selector = 'button:has-text("同意する")'
            try:
                page.wait_for_selector(accept_button_selector, state='visible', timeout=10000)
                print("Chrono24: クッキー同意ボタンを検出、クリックします...")
                page.click(accept_button_selector)
                page.wait_for_load_state('networkidle', timeout=15000)
            except PlaywrightTimeoutError:
                print("Chrono24: クッキー同意ボタンは見つかりませんでした。")

            main_content_selector = "div.sorting-wrapper"
            page.wait_for_selector(main_content_selector, state='visible', timeout=30000)

            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            result_count_element = soup.select_one("div.catalog-products-result-count > div.text-bold")
            if not result_count_element: raise Exception("総アイテム数を示す要素が見つかりません。")

            save_cookies(context, COOKIE_FILE)

            result_count_text = result_count_element.get_text(strip=True)
            total_items_match = re.search(r'[\d,]+', result_count_text)
            total_items = int(total_items_match.group().replace(',', ''))
            pages_to_scrape = math.ceil(total_items / 60)
            if max_pages != 0:
                pages_to_scrape = min(max_pages, pages_to_scrape)

            products_page1 = parse_page_data(soup)
            if products_page1: all_products.extend(products_page1)

            for page_num in range(2, pages_to_scrape + 1):
                human_like_delay(2, 5)
                page_url = f"https://www.chrono24.jp/rolex/submariner--mod1-{page_num}.htm"
                print(f"Chrono24: {page_num}ページ目を取得中...")
                page.goto(page_url, wait_until='domcontentloaded', timeout=60000)
                page.wait_for_selector(main_content_selector, state='visible', timeout=30000)
                html_content = page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                products_on_page = parse_page_data(soup)
                if products_on_page: all_products.extend(products_on_page)
                else: break

            browser.close()
            return all_products
        except Exception as e:
            print(f"Chrono24のスクレイピング中にエラーが発生しました: {e}")
            page.screenshot(path='chrono24_error_screenshot.png')
            browser.close()
            return None

def main():
    """このスクリプトを単体で実行するためのメイン関数"""
    print("--- Chrono24の単体スクレイピングを開始します ---")
    scraped_products = scrape_chrono24_submariner(max_pages=1) # 単体テスト時は1ページのみ
    if scraped_products:
        output_filename = "chrono24_scraped_data.json"
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(scraped_products, f, ensure_ascii=False, indent=2)
            print(f"\n✅ {len(scraped_products)}件のデータを '{output_filename}' に正常に出力しました。")
        except Exception as e:
            print(f"\n❌ ファイル出力中にエラーが発生しました: {e}")
    else:
        print("商品情報の取得に失敗しました。")

if __name__ == "__main__":
    main()