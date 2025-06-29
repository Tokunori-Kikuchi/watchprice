# run_all_scrapers.py

import json
import os
from datetime import datetime
import requests

# --- 各スクレイパーをインポート ---
from chrono24_scraper import scrape_chrono24_submariner
from ebay_scraper import scrape_ebay
from tokemar_scraper import scrape_tokemar
from allu_scraper import scrape_allu # ALLUを追加

def main():
    print(f"--- 全スクレイピング処理を開始します --- [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")

    all_results = []

    # --- 1. Chrono24 ---
    try:
        print("\n[1/4] Chrono24のスクレイピングを実行中...")
        chrono24_products = scrape_chrono24_submariner(max_pages=1)
        if chrono24_products:
            all_results.extend(chrono24_products)
            print(f"✅ Chrono24から {len(chrono24_products)} 件のデータを取得しました。")
    except Exception as e:
        print(f"❌ Chrono24のスクレイピング中にエラー: {e}")

    # --- 2. eBay ---
    try:
        print("\n[2/4] eBayのスクレイピングを実行中...")
        ebay_products = scrape_ebay(search_query="rolex submariner", max_pages=1)
        if ebay_products:
            all_results.extend(ebay_products)
            print(f"✅ eBayから {len(ebay_products)} 件のデータを取得しました。")
    except Exception as e:
        print(f"❌ eBayのスクレイピング中にエラー: {e}")

    # --- 3. トケマー ---
    try:
        print("\n[3/4] トケマーのスクレイピングを実行中...")
        tokemar_products = scrape_tokemar(search_query="ロレックス サブマリーナ", max_pages=1)
        if tokemar_products:
            all_results.extend(tokemar_products)
            print(f"✅ トケマーから {len(tokemar_products)} 件のデータを取得しました。")
    except Exception as e:
        print(f"❌ トケマーのスクレイピング中にエラー: {e}")

    # --- 4. ALLU ---
    try:
        print("\n[4/4] ALLUのスクレイピングを実行中...")
        allu_products = scrape_allu(search_query="ロレックス サブマリーナ", max_pages=1)
        if allu_products:
            all_results.extend(allu_products)
            print(f"✅ ALLUから {len(allu_products)} 件のデータを取得しました。")
    except Exception as e:
        print(f"❌ ALLUのスクレイピング中にエラー: {e}")

    # --- 5. 統合結果をサーバーに送信 ---
    if all_results:
        php_api_url = "https://dev.webwisewords.net/watchprice/api/php/save_watches.php"
        print(f"\n✅ 合計 {len(all_results)} 件のデータをサーバーAPIに送信しています...")

        try:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(php_api_url, data=json.dumps(all_results, ensure_ascii=False).encode('utf-8'), headers=headers, timeout=60)
            response.raise_for_status()
            print("✅ データ送信成功！")
            print("サーバーからの応答:", response.json())
        except requests.exceptions.RequestException as e:
            print(f"\n❌ サーバーへのデータ送信中にエラーが発生しました: {e}")
    else:
        print("\n有効なデータが1件も取得できなかったため、処理を終了します。")

    print(f"\n--- 全スクレイピング処理が終了しました --- [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")

if __name__ == "__main__":
    main()