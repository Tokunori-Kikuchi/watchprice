<?php
// get_watches.php - 検索条件に基づいて腕時計リストを返すAPI

// --- ヘッダー設定 ---
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");
header("Content-Type: application/json; charset=UTF-8");

// プリフライトリクエストに対応
if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    exit;
}

// --- DB接続 ---
require 'db.php';

// --- 検索条件の取得 ---
$search_term = '';
// POSTリクエストのボディからJSONデータを取得
$json_data = file_get_contents('php://input');
if (!empty($json_data)) {
    $request_data = json_decode($json_data, true);
    // 'searchTerm'というキーで検索語を受け取る
    if (isset($request_data['searchTerm'])) {
        $search_term = trim($request_data['searchTerm']);
    }
}

try {
    // --- 動的なSQLクエリの生成 ---
    $sql = "SELECT * FROM watches";
    $params = [];

    if (!empty($search_term)) {
        // 検索語がある場合、WHERE句を追加
        // nameカラムに検索語が含まれるものを部分一致で検索
        $sql .= " WHERE name LIKE ?";
        $params[] = '%' . $search_term . '%';
    }

    // ORDER BY句とLIMIT句を追加
    $sql .= " ORDER BY updated_at DESC LIMIT 100";

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $results = $stmt->fetchAll();

    // 結果をJSONで出力
    echo json_encode(['results' => $results]);

} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'データベースクエリに失敗しました。',
        'message' => $e->getMessage()
    ]);
}
?>