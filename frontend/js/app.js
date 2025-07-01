// app.js

const API_URL = 'https://dev.webwisewords.net/watchprice/api/php/get_watches.php';
const rootElement = document.getElementById('root');
const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search-input');
const priceRangeMin = document.getElementById('price-range-min');
const priceRangeMax = document.getElementById('price-range-max');
const priceRangeMinValue = document.getElementById('price-range-min-value');
const priceRangeMaxValue = document.getElementById('price-range-max-value');
const yearRangeMin = document.getElementById('year-range-min');
const yearRangeMax = document.getElementById('year-range-max');
const yearRangeMinValue = document.getElementById('year-range-min-value');
const yearRangeMaxValue = document.getElementById('year-range-max-value');
const sortSelect = document.getElementById('sort-select');
const chartArea = document.getElementById('chart-area');
const exportCsvBtn = document.getElementById('export-csv-btn');
const showFilterBtn = document.getElementById('show-filter-btn');
const closeFilterBtn = document.getElementById('close-filter-btn');
const filterPanel = document.getElementById('filter-panel');
const showChartBtn = document.getElementById('show-chart-btn');
const closeChartBtn = document.getElementById('close-chart-btn');
const chartAreaDiv = document.getElementById('chart-area');

let allWatches = [];
let chartInstance = null;
let chartMode = 'brand'; // 'brand' | 'model' | 'hist' | 'rank'
let currentSearchTerm = '';

// --- データ取得＆UI連動 ---
async function fetchAndRenderWatches(searchTerm = '') {
    rootElement.innerHTML = `
        <div class="loading-spinner-container">
            <div class="loading-spinner"></div>
            <p>検索中...</p>
        </div>
    `;
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ searchTerm: searchTerm })
        });
        if (!response.ok) throw new Error(`APIエラー: ${response.status} ${response.statusText}`);
        const data = await response.json();
        allWatches = data.results || [];
        updateUI();
    } catch (error) {
        console.error(error);
        rootElement.innerHTML = `<p>エラーが発生しました: ${error.message}</p>`;
    }
}

// --- 検索・フィルタ・ソート・グラフ描画 ---
function updateUI() {
    let filtered = allWatches.slice();
    // 検索キーワード（ブランド名・モデル名部分一致）
    if (currentSearchTerm) {
        const term = currentSearchTerm.toLowerCase();
        filtered = filtered.filter(w => (
            (w.name && w.name.toLowerCase().includes(term)) ||
            (w.brand && w.brand.toLowerCase().includes(term)) ||
            (w.model && w.model.toLowerCase().includes(term))
        ));
    }
    // ブランドフィルタ
    const brandCheckboxes = document.querySelectorAll('.brand-checkbox');
    if (brandCheckboxes.length > 0) {
        const selectedBrands = Array.from(brandCheckboxes).filter(cb => cb.checked).map(cb => cb.value);
        if (selectedBrands.length > 0) {
            filtered = filtered.filter(w =>
                selectedBrands.some(brand =>
                    (w.name && w.name.includes(brand)) || (w.brand && w.brand.includes(brand))
                )
            );
        }
    }
    // 価格帯
    const minPrice = Number(priceRangeMin.value) || 0;
    const maxPrice = Number(priceRangeMax.value) || 10000000;
    priceRangeMinValue.textContent = `${minPrice.toLocaleString()}円`;
    priceRangeMaxValue.textContent = `${maxPrice.toLocaleString()}円`;
    filtered = filtered.filter(w => {
        const price = Number(w.price) || 0;
        return price >= minPrice && price <= maxPrice;
    });
    // 年代
    const minYear = Number(yearRangeMin.value) || 1950;
    const maxYear = Number(yearRangeMax.value) || 2024;
    yearRangeMinValue.textContent = `${minYear}年`;
    yearRangeMaxValue.textContent = `${maxYear}年`;
    filtered = filtered.filter(w => {
        if (!w.year) return true;
        return Number(w.year) >= minYear && Number(w.year) <= maxYear;
    });
    // 並び替え
    switch (sortSelect.value) {
        case 'newest':
            filtered.sort((a, b) => (b.year || 0) - (a.year || 0)); break;
        case 'oldest':
            filtered.sort((a, b) => (a.year || 9999) - (b.year || 9999)); break;
        case 'lowprice':
            filtered.sort((a, b) => Number(a.price) - Number(b.price)); break;
        case 'highprice':
            filtered.sort((a, b) => Number(b.price) - Number(a.price)); break;
    }
    renderCards(filtered);
    renderChart(filtered);
}

// --- ブランドチェックボックスのイベントリスナーを再バインド ---
function bindBrandCheckboxListeners() {
    const brandCheckboxes = document.querySelectorAll('.brand-checkbox');
    brandCheckboxes.forEach(cb => {
        cb.removeEventListener('change', updateUI);
        cb.addEventListener('change', updateUI);
    });
}

// --- 検索フォーム ---
searchForm.addEventListener('submit', (event) => {
    event.preventDefault();
    currentSearchTerm = searchInput.value.trim();
    fetchAndRenderWatches(currentSearchTerm);
});

// --- スライダー・セレクト ---
priceRangeMin.addEventListener('input', updateUI);
priceRangeMax.addEventListener('input', updateUI);
yearRangeMin.addEventListener('input', updateUI);
yearRangeMax.addEventListener('input', updateUI);
sortSelect.addEventListener('change', updateUI);

// --- 検索条件パネルの表示/非表示 ---
if (showFilterBtn && closeFilterBtn && filterPanel) {
    showFilterBtn.addEventListener('click', () => {
        filterPanel.style.display = 'block';
        filterPanel.classList.remove('hide');
        bindBrandCheckboxListeners();
        updateUI();
    });
    closeFilterBtn.addEventListener('click', () => {
        filterPanel.classList.add('hide');
        setTimeout(() => {
            filterPanel.style.display = 'none';
            filterPanel.classList.remove('hide');
        }, 400);
    });
}

// --- グラフエリアの表示/非表示 ---
if (showChartBtn && closeChartBtn && chartAreaDiv) {
    showChartBtn.addEventListener('click', () => {
        chartAreaDiv.style.display = 'block';
        chartAreaDiv.classList.remove('hide');
    });
    closeChartBtn.addEventListener('click', () => {
        chartAreaDiv.classList.add('hide');
        setTimeout(() => {
            chartAreaDiv.style.display = 'none';
            chartAreaDiv.classList.remove('hide');
        }, 400);
    });
}

// --- CSVエクスポート ---
if (exportCsvBtn) {
    exportCsvBtn.addEventListener('click', exportToCsv);
}

function getFilteredWatches() {
    // 現在のフィルタ条件でデータを返す（CSV用）
    let filtered = allWatches.slice();
    if (currentSearchTerm) {
        const term = currentSearchTerm.toLowerCase();
        filtered = filtered.filter(w => (
            (w.name && w.name.toLowerCase().includes(term)) ||
            (w.brand && w.brand.toLowerCase().includes(term)) ||
            (w.model && w.model.toLowerCase().includes(term))
        ));
    }
    const selectedBrands = Array.from(document.querySelectorAll('.brand-checkbox:checked')).map(cb => cb.value);
    if (selectedBrands.length > 0) {
        filtered = filtered.filter(w =>
            selectedBrands.some(brand =>
                (w.name && w.name.includes(brand)) || (w.brand && w.brand.includes(brand))
            )
        );
    }
    const minPrice = Number(priceRangeMin.value) || 0;
    const maxPrice = Number(priceRangeMax.value) || 10000000;
    filtered = filtered.filter(w => {
        const price = Number(w.price) || 0;
        return price >= minPrice && price <= maxPrice;
    });
    const minYear = Number(yearRangeMin.value) || 1950;
    const maxYear = Number(yearRangeMax.value) || 2024;
    filtered = filtered.filter(w => {
        if (!w.year) return true;
        return Number(w.year) >= minYear && Number(w.year) <= maxYear;
    });
    return filtered;
}

function exportToCsv() {
    const watches = getFilteredWatches();
    if (!watches.length) {
        alert('エクスポートするデータがありません。');
        return;
    }
    const headers = ['name', 'brand', 'model', 'price', 'year', 'site_name', 'url', 'image_url'];
    const csvRows = [headers.join(',')];
    watches.forEach(w => {
        const row = headers.map(h => {
            let val = w[h] !== undefined ? w[h] : '';
            if (typeof val === 'string') {
                val = '"' + val.replace(/"/g, '""') + '"';
            }
            return val;
        });
        csvRows.push(row.join(','));
    });
    const csv = csvRows.join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'watches_export.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// --- カード描画 ---
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
                if (watch.name.toLowerCase().startsWith(b.toLowerCase())) {
                    brand = b.toUpperCase() === 'TUDOR' ? 'Tudor' : b;
                    model = watch.name.substring(b.length).trim();
                    break;
                }
            }
        }
        const imageContainer = document.createElement('div');
        imageContainer.className = 'card-image-container';
        const siteLabel = document.createElement('span');
        siteLabel.className = 'site-label';
        siteLabel.textContent = watch.site_name || 'Unknown';
        const image = document.createElement('img');
        image.className = 'card-image';
        if (watch.image_url) {
            image.src = watch.image_url;
            image.alt = watch.name;
        } else {
            const noImageDiv = document.createElement('div');
            noImageDiv.className = 'card-image no-image';
            imageContainer.appendChild(noImageDiv);
        }
        if (watch.image_url) {
            imageContainer.appendChild(image);
        }
        imageContainer.appendChild(siteLabel);
        card.innerHTML = `
            ${imageContainer.outerHTML}
            <div class="card-content">
                <h3>${brand}</h3>
                <p class="model">${model}</p>
                <p class="price">¥${Number(watch.price).toLocaleString()}</p>
            </div>
        `;
        rootElement.appendChild(card);
    });
}

// --- グラフ描画 ---
function renderChart(watches) {
    if (!chartArea) return;
    let canvas = document.getElementById('priceChart');
    if (!canvas) {
        canvas = document.createElement('canvas');
        canvas.id = 'priceChart';
        canvas.height = 120;
        chartArea.appendChild(canvas);
    } else {
        canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
    }
    const ctx = canvas.getContext('2d');
    if (chartInstance) chartInstance.destroy();
    const selectedBrands = Array.from(document.querySelectorAll('.brand-checkbox:checked')).map(cb => cb.value);
    if (chartMode === 'brand') {
        const yearMap = {};
        watches.forEach(w => {
            const y = w.year || '不明';
            if (!yearMap[y]) yearMap[y] = [];
            yearMap[y].push(Number(w.price));
        });
        const years = Object.keys(yearMap).filter(y => y !== '不明').sort();
        const avgPrices = years.map(y => {
            const arr = yearMap[y];
            return arr.reduce((a, b) => a + b, 0) / arr.length;
        });
        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: years,
                datasets: [{
                    label: '平均価格（円）',
                    data: avgPrices,
                    borderColor: '#D4AF37',
                    backgroundColor: 'rgba(212,175,55,0.15)',
                    tension: 0.3,
                    pointRadius: 4,
                    pointBackgroundColor: '#D4AF37',
                    fill: true,
                }]
            },
            options: {
                plugins: {
                    legend: { display: true, labels: { color: '#fff' } },
                },
                scales: {
                    x: { ticks: { color: '#fff', maxRotation: 60, minRotation: 30 }, grid: { color: 'rgba(255,255,255,0.1)' } },
                    y: { ticks: { color: '#fff' }, grid: { color: 'rgba(255,255,255,0.1)' } }
                },
                responsive: true,
            }
        });
    } else if (chartMode === 'model') {
        const modelMap = {};
        watches.forEach(w => {
            let model = '不明';
            if (w.name) {
                const matchedBrand = selectedBrands.find(b => w.name.startsWith(b));
                if (matchedBrand) {
                    model = w.name.replace(matchedBrand, '').trim();
                } else {
                    model = w.name;
                }
            }
            if (!modelMap[model]) modelMap[model] = [];
            modelMap[model].push(Number(w.price));
        });
        const models = Object.keys(modelMap).filter(m => m && m !== '不明');
        const avgPrices = models.map(m => {
            const arr = modelMap[m];
            return arr.reduce((a, b) => a + b, 0) / arr.length;
        });
        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: models,
                datasets: [{
                    label: 'モデル別平均価格（円）',
                    data: avgPrices,
                    backgroundColor: 'rgba(212,175,55,0.7)',
                    borderColor: '#D4AF37',
                    borderWidth: 1,
                }]
            },
            options: {
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    x: { ticks: { color: '#fff', maxRotation: 60, minRotation: 30 }, grid: { color: 'rgba(255,255,255,0.1)' } },
                    y: { ticks: { color: '#fff' }, grid: { color: 'rgba(255,255,255,0.1)' } }
                },
                responsive: true,
            }
        });
    } else if (chartMode === 'hist') {
        const binSize = 500000;
        const maxPrice = Math.max(...watches.map(w => Number(w.price) || 0), 0);
        const bins = [];
        const labels = [];
        for (let p = 0; p <= maxPrice + binSize; p += binSize) {
            bins.push(0);
            labels.push(`〜${(p + binSize).toLocaleString()}円`);
        }
        watches.forEach(w => {
            const price = Number(w.price) || 0;
            const idx = Math.floor(price / binSize);
            if (bins[idx] !== undefined) bins[idx]++;
        });
        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '商品数',
                    data: bins,
                    backgroundColor: 'rgba(212,175,55,0.7)',
                    borderColor: '#D4AF37',
                    borderWidth: 1,
                }]
            },
            options: {
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    x: { ticks: { color: '#fff', maxRotation: 60, minRotation: 30 }, grid: { color: 'rgba(255,255,255,0.1)' } },
                    y: { ticks: { color: '#fff' }, grid: { color: 'rgba(255,255,255,0.1)' } }
                },
                responsive: true,
            }
        });
    } else if (chartMode === 'rank') {
        if (selectedBrands.length === 0) {
            const brandMap = {};
            watches.forEach(w => {
                let brand = '不明';
                if (w.brand) {
                    brand = w.brand;
                } else if (w.name) {
                    brand = w.name.split(' ')[0];
                }
                if (!brandMap[brand]) brandMap[brand] = [];
                brandMap[brand].push(Number(w.price));
            });
            const brands = Object.keys(brandMap).filter(b => b && b !== '不明');
            const avgPrices = brands.map(b => {
                const arr = brandMap[b];
                return arr.reduce((a, b) => a + b, 0) / arr.length;
            });
            const sorted = brands.map((b, i) => ({ brand: b, avg: avgPrices[i] }))
                .sort((a, b) => b.avg - a.avg)
                .slice(0, 10);
            chartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: sorted.map(x => x.brand),
                    datasets: [{
                        label: '平均価格（円）',
                        data: sorted.map(x => x.avg),
                        backgroundColor: 'rgba(212,175,55,0.7)',
                        borderColor: '#D4AF37',
                        borderWidth: 1,
                    }]
                },
                options: {
                    plugins: {
                        legend: { display: false },
                    },
                    scales: {
                        x: { ticks: { color: '#fff', maxRotation: 60, minRotation: 30 }, grid: { color: 'rgba(255,255,255,0.1)' } },
                        y: { ticks: { color: '#fff' }, grid: { color: 'rgba(255,255,255,0.1)' } }
                    },
                    responsive: true,
                }
            });
        } else {
            const modelMap = {};
            watches.forEach(w => {
                let model = '不明';
                if (w.name) {
                    const matchedBrand = selectedBrands.find(b => w.name.startsWith(b));
                    if (matchedBrand) {
                        model = w.name.replace(matchedBrand, '').trim();
                    } else {
                        model = w.name;
                    }
                }
                if (!modelMap[model]) modelMap[model] = [];
                modelMap[model].push(Number(w.price));
            });
            const models = Object.keys(modelMap).filter(m => m && m !== '不明');
            const avgPrices = models.map(m => {
                const arr = modelMap[m];
                return arr.reduce((a, b) => a + b, 0) / arr.length;
            });
            const sorted = models.map((m, i) => ({ model: m, avg: avgPrices[i] }))
                .sort((a, b) => b.avg - a.avg)
                .slice(0, 10);
            chartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: sorted.map(x => x.model),
                    datasets: [{
                        label: 'モデル別平均価格（円）',
                        data: sorted.map(x => x.avg),
                        backgroundColor: 'rgba(212,175,55,0.7)',
                        borderColor: '#D4AF37',
                        borderWidth: 1,
                    }]
                },
                options: {
                    plugins: {
                        legend: { display: false },
                    },
                    scales: {
                        x: { ticks: { color: '#fff', maxRotation: 60, minRotation: 30 }, grid: { color: 'rgba(255,255,255,0.1)' } },
                        y: { ticks: { color: '#fff' }, grid: { color: 'rgba(255,255,255,0.1)' } }
                    },
                    responsive: true,
                }
            });
        }
    }
}

// --- 初期値設定・初回データ取得 ---
priceRangeMin.value = 0;
priceRangeMax.value = 10000000;
yearRangeMin.value = 1950;
yearRangeMax.value = 2024;
fetchAndRenderWatches();