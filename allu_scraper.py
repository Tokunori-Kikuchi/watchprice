from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import json
import re
import time
import os
import random

# --- 定数とヘルパー関数 ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def human_like_delay(min_sec=1.5, max_sec=4.0):
    """人間らしいランダムな待機時間を生成する"""
    time.sleep(random.uniform(min_sec, max_sec))

def parse_allu_page(soup):
    """ALLUの検索結果ページから商品情報を抽出する"""
    products = []
    items = soup.select('div.css-1k9g5l3 > a')

    for item in items:
        sold_out_tag = item.select_one('div.css-1bsm34')
        if sold_out_tag:
            continue

        url = "https://allu-official.com" + item['href']
        name_tag = item.select_one('p.css-1w3q2er')
        price_tag = item.select_one('p.css-1pfq2d4')
        image_tag = item.select_one('img.css-1h29x4o')

        if not all([name_tag, price_tag, image_tag]):
            continue

        name = name_tag.get_text(strip=True)
        image_url = image_tag.get('src')
        price_text = price_tag.get_text(strip=True).replace(',', '').replace('¥', '')
        price_match = re.search(r'[\d]+', price_text)
        price = int(price_match.group()) if price_match else 0

        if price == 0:
            continue

        products.append({
            'name': name, 'price': price, 'url': url,
            'image_url': image_url, 'site_name': 'ALLU'
        })
    return products

def scrape_allu(search_query="ロレックス サブマリーナ", max_pages=2):
    """
    メニューを辿ってブランドページにアクセスし、在庫フィルタを適用します。
    Inspectorで取得したセレクタでロレックスリンクをクリック。
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
            # ブランド一覧ページを直接開く
            market_url = "https://allu-official.com/jp/ja/market/"
            print(f"ALLUブランド一覧ページにアクセス中: {market_url}")
            page.goto(market_url, wait_until='networkidle', timeout=60000)

            # ロレックスリンクをInspectorで取得したセレクタでクリック
            print("ブランド一覧から『ロレックス』リンクをクリックしています...")
            page.wait_for_selector('a', state='visible', timeout=15000)  # リンクが出るまで待つ
            with page.expect_navigation(wait_until='domcontentloaded', timeout=60000):
                page.get_by_role("link", name="ロレックス").first.click()

            print("ロレックス商品一覧ページに遷移しました。")

            # 在庫ありフィルターを適用
            in_stock_button_selector = 'a:has-text("在庫あり")'
            print("『在庫あり』フィルターをクリックしています...")
            page.wait_for_selector(in_stock_button_selector, state='visible', timeout=15000)
            with page.expect_navigation(wait_until='domcontentloaded', timeout=60000):
                page.click(in_stock_button_selector)

            print("フィルター適用完了。")

            # 商品リストまたは「見つかりません」メッセージを待つ
            page.wait_for_selector('div.css-1k9g5l3, div.css-191rp51', timeout=30000)

            if "お探しの条件に合う商品はございませんでした" in page.content():
                print("ALLU: 検索条件に合致する商品が見つかりませんでした。")
                browser.close()
                return all_products

            pages_to_scrape = max_pages if max_pages != 0 else 100
            for page_num in range(1, pages_to_scrape + 1):
                if page_num > 1:
                    print(f"\nALLU {page_num}ページ目を取得中...")
                    try:
                        next_button_selector = 'a:has-text("Next")'
                        page.wait_for_selector(next_button_selector, state='visible', timeout=5000)
                        with page.expect_navigation(wait_until='domcontentloaded', timeout=60000):
                            page.click(next_button_selector)
                        page.wait_for_selector('div.css-1k9g5l3', timeout=30000)
                    except PlaywrightTimeoutError:
                        print("「Next」ボタンが見つかりません。最終ページと判断します。")
                        break

                human_like_delay()
                html_content = page.content()
                soup = BeautifulSoup(html_content, 'html.parser')

                products_on_page = parse_allu_page(soup)
                if not products_on_page:
                    print("商品リストの解析に失敗しました。")
                    break

                all_products.extend(products_on_page)
                print(f"{page_num}ページ目から {len(products_on_page)} 件取得しました。")

            browser.close()
            return all_products

        except Exception as e:
            print(f"ALLUのスクレイピング中にエラーが発生しました: {e}")
            page.screenshot(path='allu_error_screenshot.png')
            browser.close()
            return None

def main():
    """このスクリプトを単体で実行するためのメイン関数"""
    print("--- ALLUの単体スクレイピングを開始します ---")
    scraped_products = scrape_allu(max_pages=1)
    if scraped_products:
        output_filename = "allu_scraped_data.json"
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(scraped_products, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 合計{len(scraped_products)}件のデータを '{output_filename}' に正常に出力しました。")
        except Exception as e:
            print(f"\n❌ ファイル出力中にエラーが発生しました: {e}")
    else:
        print("商品情報の取得に失敗しました。")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 1. ALLUのトップページへアクセス
        page.goto("https://allu-official.com/jp/ja/market/")

        # 2. ここに必要な操作（例：メニュークリック等）を記述
        # 例: page.click("text=BRAND") など

        # 3. ブランド一覧ページに遷移した直後にデバッグポイントを挿入
        page.pause()  # ← ここでPlaywright Inspectorが起動し、処理が一時停止します

        # 4. 以降の操作はInspectorでセレクタを特定後に記述

if __name__ == "__main__":
    main()