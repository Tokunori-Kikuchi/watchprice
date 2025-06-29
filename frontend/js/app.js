// app.js

const API_URL = 'https://dev.webwisewords.net/watchprice/api/php/get_watches.php';
const rootElement = document.getElementById('root');
const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search-input');

/**
 * 検索条件に基づいて腕時計データを取得し、表示を更新する
 * @param {string} searchTerm - 検索キーワード
 */
async function fetchAndRenderWatches(searchTerm = '') {
    // 検索中はローディング表示
    rootElement.innerHTML = `
        <div class="loading-spinner-container">
            <div class="loading-spinner"></div>
            <p>検索中...</p>
        </div>
    `;

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            // 検索キーワードをJSON形式で送信
            body: JSON.stringify({ searchTerm: searchTerm })
        });

        if (!response.ok) {
            throw new Error(`APIエラー: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        if (!data.results || data.results.length === 0) {
            rootElement.innerHTML = '<p>該当するデータが見つかりませんでした。</p>';
            return;
        }

        renderCards(data.results);

    } catch (error) {
        console.error(error);
        rootElement.innerHTML = `<p>エラーが発生しました: ${error.message}</p>`;
    }
}

/**
 * 腕時計データの配列からカードを生成して表示する
 * @param {Array} watches - 腕時計データの配列
 */
function renderCards(watches) {
    rootElement.innerHTML = '';
    watches.forEach(watch => {
        const card = document.createElement('a');
        card.className = 'card';
        card.href = watch.url;
        card.target = '_blank';

        let brand = '情報なし';
        let model = watch.name || 'モデル情報なし';
        const knownBrands = ['Rolex', 'Omega', 'Seiko', 'Patek Philippe', 'Audemars Piguet', 'Tudor', 'TUDOR'];

        if (watch.name) {
            for (const b of knownBrands) {
                // 大文字小文字を区別せずに比較
                if (watch.name.toLowerCase().startsWith(b.toLowerCase())) {
                    brand = b.toUpperCase() === 'TUDOR' ? 'Tudor' : b; // TUDORはTudorと表示
                    model = watch.name.substring(b.length).trim();
                    break;
                }
            }
        }

        // --- ▼▼▼ ここから修正 ▼▼▼ ---

        // 画像コンテナを作成
        const imageContainer = document.createElement('div');
        imageContainer.className = 'card-image-container';

        // サイト名ラベルを作成
        const siteLabel = document.createElement('span');
        siteLabel.className = 'site-label';
        siteLabel.textContent = watch.site_name || 'Unknown';

        // 画像を作成
        const image = document.createElement('img');
        image.className = 'card-image';
        if (watch.image_url) {
            image.src = watch.image_url;
            image.alt = watch.name;
        } else {
            // 画像がない場合の代替処理
            const noImageDiv = document.createElement('div');
            noImageDiv.className = 'card-image no-image';
            imageContainer.appendChild(noImageDiv);
        }

        // 画像コンテナに画像とラベルを追加
        if (watch.image_url) {
            imageContainer.appendChild(image);
        }
        imageContainer.appendChild(siteLabel);

        // カードの内部HTMLを生成
        card.innerHTML = `
            ${imageContainer.outerHTML}
            <div class="card-content">
                <h3>${brand}</h3>
                <p class="model">${model}</p>
                <p class="price">¥${Number(watch.price).toLocaleString()}</p>
            </div>
        `;
        // --- ▲▲▲ ここまで修正 ▲▲▲ ---

        rootElement.appendChild(card);
    });
}

// --- イベントリスナーの設定 ---

// フォームが送信されたときの処理
searchForm.addEventListener('submit', (event) => {
    event.preventDefault(); // ページの再読み込みをキャンセル
    const searchTerm = searchInput.value.trim();
    fetchAndRenderWatches(searchTerm);
});

// ページ読み込み時に、まず全件表示（検索キーワードなし）を実行
fetchAndRenderWatches();