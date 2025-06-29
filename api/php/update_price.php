<?php
// update_prices.php

ini_set('display_errors', 1);
error_reporting(E_ALL);

header('Content-Type: application/json; charset=utf-8');
require 'db.php';

$json_file_path = __DIR__ . '/scraped_data.json';

if (!file_exists($json_file_path)) {
    http_response_code(404);
    echo json_encode(['error' => 'データファイルが見つかりません。', 'path' => $json_file_path]);
    exit;
}

$json_data = file_get_contents($json_file_path);
$products = json_decode($json_data, true);

if (json_last_error() !== JSON_ERROR_NONE) {
    http_response_code(500);
    echo json_encode(['error' => 'JSONデータの解析に失敗しました。', 'json_error' => json_last_error_msg()]);
    exit;
}

if (empty($products)) {
    echo json_encode(['message' => 'データが空です。処理をスキップしました。']);
    exit;
}

$inserted_count = 0;
$updated_count = 0;
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

// --- ▼▼▼ SQLとロジックを修正 ▼▼▼ ---
foreach ($products as $item) {
    try {
        if (empty($item['url']) || empty($item['price'])) {
            continue;
        }

        // ON DUPLICATE KEY UPDATE を使用して、INSERTとUPDATEを1つのクエリで実現
        // 事前に `url` カラムにUNIQUE KEY制約が必要です。
        $sql = "
            INSERT INTO watches (name, price, url, image_url, site_name, created_at, updated_at)
            VALUES (:name, :price, :url, :image_url, :site_name, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                price = VALUES(price),
                image_url = VALUES(image_url),
                updated_at = NOW()
        ";

        $stmt = $pdo->prepare($sql);

        $stmt->execute([
            ':name'      => $item['name'],
            ':price'     => $item['price'],
            ':url'       => $item['url'],
            ':image_url' => $item['image_url'],
            ':site_name' => 'Chrono24' // 取得元サイト名を指定
        ]);

        // rowCount()で更新か挿入かを判定
        if ($stmt->rowCount() > 0) {
            // 実際にはrowCountはINSERTで1、UPDATEで2(削除+挿入)を返すことがあるため、
            // 厳密なカウントより処理成功の指標として利用
            $inserted_count++;
        }

    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode([
            'error' => 'DB処理中にエラーが発生しました。',
            'message' => $e->getMessage(),
            'item' => $item
        ]);
        exit;
    }
}
// --- ▲▲▲ ここまで修正 ▲▲▲ ---

echo json_encode([
    'status' => 'success',
    'message' => 'データ更新完了',
    'processed_count' => $inserted_count, // 処理した件数として報告
]);