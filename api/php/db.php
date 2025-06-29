<?php
// db.php - MySQL接続設定

// -----↓ここを自分の設定に書き換える↓-----
$host = 'localhost'; // Xserverの場合は指定されたホスト名
$db   = 'xs910068_watchprice'; // あなたのデータベース名
$user = 'xs910068_wprice';      // あなたのデータベースユーザー名
$pass = 'WAS4sheep7teen';  // あなたのデータベースパスワード
// -----↑ここまで↑-------------------------

$charset = 'utf8mb4';

$dsn = "mysql:host=$host;dbname=$db;charset=$charset";
$options = [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION, // エラー時に例外を投げる
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,       // 連想配列形式で取得
    PDO::ATTR_EMULATE_PREPARES   => false,                  // SQLインジェクション対策
];

try {
    // データベースに接続
    $pdo = new PDO($dsn, $user, $pass, $options);
} catch (\PDOException $e) {
    // 接続失敗時はエラーメッセージを出して終了
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['error' => 'データベース接続に失敗しました。']);
    exit;
}
?>