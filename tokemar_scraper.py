from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import json
import re
import time
import os
import random

# --- 定数とヘルパー関数 ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

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

def human_like_delay(min_sec=1.5, max_sec=4.0):
    """人間らしいランダムな待機時間を生成する"""
    time.sleep(random.uniform(min_sec, max_sec))

def parse_tokemar_page(soup):
    """トケマーの検索結果ページから商品情報を抽出する"""
    products = []
    items = soup.select('div.ty-grid-list__item')

    for item in items:
        name_tag = item.select_one('a.product-title')
        price_tag = item.select_one('span.ty-price-num')
        url_tag = item.select_one('div.ty-grid-list__image > a')
        image_tag = item.select_one('img.ty-pict')

        if not all([name_tag, price_tag, url_tag, image_tag]):
            continue

        name = name_tag.get_text(strip=True)
        url = url_tag['href']
        image_url = image_tag.get('src')

        price_text = price_tag.get_text(strip=True).replace(',', '')
        price_match = re.search(r'[\d]+', price_text)
        price = int(price_match.group()) if price_match else 0

        if price == 0:
            continue

        products.append({
            'name': name,
            'price': price,
            'url': url,
            'image_url': image_url,
            'site_name': 'トケマー'
        })

    return products

def scrape_tokemar(search_query="ロレックス サブマリーナ", max_pages=2):
    """
    検索フォームの親要素を待機し、確実にフォームを操作します。
    """
    all_products = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            locale='ja-JP',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            print("トケマーのトップページにアクセス中...")
            page.goto("https://www.tokemar.com/", wait_until='networkidle', timeout=60000)

            # 検索フォームを囲む、より大きなコンテナが表示されるのを待つ
            search_container_selector = 'div.ty-search-block'
            print(f"検索コンテナ({search_container_selector})の表示を待機中...")
            page.wait_for_selector(search_container_selector, state='visible', timeout=20000)

            # 正しいセレクタで入力フォームを特定
            search_input_selector = 'input[name="hint_q"]'

            print(f"検索フォームに「{search_query}」と入力しています...")
            page.fill(search_input_selector, search_query)

            print("検索を実行しています...")
            with page.expect_navigation(wait_until='domcontentloaded', timeout=60000):
                page.press(search_input_selector, 'Enter')

            print("検索結果ページの読み込み完了。")

            # 商品リストまたは「見つかりません」メッセージを待つ
            page.wait_for_selector('div.grid-list, p.ty-no-items', timeout=30000)

            if page.locator('p.ty-no-items').is_visible():
                print("検索条件に合致する商品が見つかりませんでした。")
                browser.close()
                return all_products

            pages_to_scrape = max_pages if max_pages != 0 else 100
            for page_num in range(1, pages_to_scrape + 1):
                if page_num > 1:
                    print(f"\nトケマー {page_num}ページ目を取得中...")
                    try:
                        next_button_selector = 'a.ty-pagination__next'
                        with page.expect_navigation(wait_until='domcontentloaded', timeout=60000):
                            page.click(next_button_selector)
                        page.wait_for_selector('div.grid-list', timeout=30000)
                    except PlaywrightTimeoutError:
                        print("「次へ」ボタンが見つかりません。最終ページと判断します。")
                        break

                human_like_delay()
                html_content = page.content()
                soup = BeautifulSoup(html_content, 'html.parser')

                products_on_page = parse_tokemar_page(soup)
                if not products_on_page:
                    print("商品リストの解析に失敗しました。")
                    break

                all_products.extend(products_on_page)
                print(f"{page_num}ページ目から {len(products_on_page)} 件取得しました。")

            browser.close()
            return all_products

        except Exception as e:
            print(f"トケマーのスクレイピング中にエラーが発生しました: {e}")
            page.screenshot(path='tokemar_error_screenshot.png')
            browser.close()
            return None

def calc_json_bytes(data):
    return len(json.dumps(data, ensure_ascii=False).encode('utf-8'))

def scrape_tokemar_priority_brands(max_pages=2, max_total_bytes=4_500_000_000, already_bytes=0):
    all_products = []
    total_bytes = already_bytes
    for brand in PRIORITY_BRANDS:
        if total_bytes >= max_total_bytes:
            print("容量上限に達したためトケマーの取得を停止します。")
            break
        print(f"\n--- トケマーブランド検索: {brand} ---")
        products = scrape_tokemar(search_query=brand, max_pages=max_pages)
        if products:
            all_products.extend(products)
            total_bytes += calc_json_bytes(products)
            print(f"トケマー: {brand} で {len(products)}件取得、累計 {total_bytes/1_000_000:.2f}MB")
    return all_products

def main():
    """このスクリプトを単体で実行するためのメイン関数"""
    print("--- トケマーの単体スクレイピングを開始します ---")
    scraped_products = scrape_tokemar(max_pages=1)
    if scraped_products:
        output_filename = "tokemar_scraped_data.json"
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