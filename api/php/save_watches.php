<?php
// save_watches.php - データを受け取ってDBに保存するAPI

header('Content-Type: application/json; charset=UTF-8');
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    exit;
}

require 'db.php';

$json_data = file_get_contents('php://input');
$products = json_decode($json_data, true);

if (json_last_error() !== JSON_ERROR_NONE || empty($products)) {
    http_response_code(400);
    echo json_encode(['error' => 'データが空か、JSON形式が正しくありません。']);
    exit;
}

$processed_count = 0;
$error_items = [];

try {
    // --- ▼▼▼ SQLのUPDATE句を修正 ▼▼▼ ---
    $sql = "
        INSERT INTO watches (name, price, url, image_url, site_name, created_at, updated_at)
        VALUES (:name, :price, :url, :image_url, :site_name, NOW(), NOW())
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            price = VALUES(price),
            image_url = VALUES(image_url),
            site_name = VALUES(site_name), -- この行を追加
            updated_at = NOW()
    ";
    // --- ▲▲▲ ここまで修正 ▲▲▲ ---

    $stmt = $pdo->prepare($sql);

    foreach ($products as $item) {
        if (isset($item['name'], $item['price'], $item['url'])) {
            $stmt->execute([
                ':name'      => $item['name'],
                ':price'     => (int)$item['price'],
                ':url'       => $item['url'],
                ':image_url' => $item['image_url'] ?? null,
                ':site_name' => $item['site_name'] ?? 'Unknown'
            ]);
            $processed_count++;
        } else {
            $error_items[] = $item;
        }
    }

    $response = [
        'status' => 'success',
        'message' => "{$processed_count}件のデータを処理しました。"
    ];
    if (!empty($error_items)) {
        $response['warnings'] = '一部のデータは必須項目が不足していたためスキップされました。';
    }
    echo json_encode($response);

} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'データベースへの保存中にエラーが発生しました。', 'details' => $e->getMessage()]);
}
?>