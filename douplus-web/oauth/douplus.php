<?php
/**
 * DOU+ 抖音OAuth授权回调处理
 * 
 * 回调地址: https://douplus.easymai.cn/oauth/douplus.php
 * 
 * 部署位置：/opt/douplus/douplus-web/dist/oauth/douplus.php
 */

// 配置信息（与.env中保持一致）
define('APP_ID', '1854346912597002');
define('APP_SECRET', '76962f707eec1dfb0ae30995696b0a9d4c9a437e');
define('API_BASE_URL', 'https://ad.oceanengine.com/open_api/oauth2');
define('LOG_FILE', '/tmp/douplus_oauth_debug.log');

// 数据库配置
define('DB_HOST', '127.0.0.1');
define('DB_NAME', 'douplus');
define('DB_USER', 'douplus');
define('DB_PASS', 'Asd123000');

// 错误处理
error_reporting(E_ALL);
ini_set('display_errors', 0);

/**
 * 记录调试日志
 */
function debugLog($message, $data = null) {
    $log = date('Y-m-d H:i:s') . ' - ' . $message;
    if ($data !== null) {
        $log .= "\n" . json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    }
    $log .= "\n" . str_repeat('-', 50) . "\n";
    file_put_contents(LOG_FILE, $log, FILE_APPEND);
    error_log($message . ($data ? ': ' . json_encode($data, JSON_UNESCAPED_UNICODE) : ''));
}

/**
 * 数据库连接
 */
function getDB() {
    try {
        $pdo = new PDO(
            'mysql:host=' . DB_HOST . ';dbname=' . DB_NAME . ';charset=utf8mb4',
            DB_USER,
            DB_PASS,
            [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
        );
        return $pdo;
    } catch (PDOException $e) {
        throw new Exception('数据库连接失败: ' . $e->getMessage());
    }
}

/**
 * 调用API
 */
function callApi($url, $params = [], $method = 'GET', $headers = []) {
    $ch = curl_init();
    
    if ($method === 'GET' && !empty($params)) {
        $url .= '?' . http_build_query($params);
    }
    
    $defaultHeaders = ['Content-Type: application/json'];
    $allHeaders = array_merge($defaultHeaders, $headers);
    
    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_HTTPHEADER => $allHeaders
    ]);
    
    if ($method === 'POST') {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($params));
    }
    
    $response = curl_exec($ch);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        throw new Exception('API请求失败: ' . $error);
    }
    
    return json_decode($response, true);
}

/**
 * 用授权码换取access_token
 */
function getAccessToken($authCode) {
    $url = API_BASE_URL . '/access_token/';
    $params = [
        'app_id' => APP_ID,
        'secret' => APP_SECRET,
        'grant_type' => 'auth_code',
        'auth_code' => $authCode
    ];
    
    $result = callApi($url, $params, 'POST');
    
    // 记录完整的token响应
    debugLog('Access Token Response', $result);
    
    if (!isset($result['data']) || empty($result['data']['access_token'])) {
        $errMsg = $result['message'] ?? json_encode($result);
        throw new Exception('获取access_token失败: ' . $errMsg);
    }
    
    return $result['data'];
}

/**
 * 获取广告主信息
 */
function getAdvertiserInfo($accessToken, $advertiserId) {
    $url = 'https://ad.oceanengine.com/open_api/2/advertiser/info/';
    $params = ['advertiser_ids' => json_encode([(int)$advertiserId])];
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url . '?' . http_build_query($params),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_HTTPHEADER => [
            'Access-Token: ' . $accessToken,
            'Content-Type: application/json'
        ]
    ]);
    
    $response = curl_exec($ch);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        debugLog('Advertiser Info Error', $error);
        return null;
    }
    
    $result = json_decode($response, true);
    
    // 详细日志
    debugLog('Advertiser Info Response', $result);
    
    if (isset($result['data']['list'][0])) {
        return $result['data']['list'][0];
    }
    
    return null;
}

/**
 * 获取用户信息（通过user/info接口 - 新版）
 */
function getUserInfoV2($accessToken) {
    $url = 'https://api.oceanengine.com/open_api/2/user/info/';
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_HTTPHEADER => [
            'Access-Token: ' . $accessToken,
            'Content-Type: application/json'
        ]
    ]);
    
    $response = curl_exec($ch);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        debugLog('User Info V2 Error', $error);
        return null;
    }
    
    $result = json_decode($response, true);
    debugLog('User Info V2 Response', $result);
    
    if (isset($result['data'])) {
        return $result['data'];
    }
    
    return null;
}

/**
 * 获取用户信息（通过user/info接口）
 */
function getUserInfo($accessToken) {
    $url = 'https://ad.oceanengine.com/open_api/2/user/info/';
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_HTTPHEADER => [
            'Access-Token: ' . $accessToken,
            'Content-Type: application/json'
        ]
    ]);
    
    $response = curl_exec($ch);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        debugLog('User Info Error', $error);
        return null;
    }
    
    $result = json_decode($response, true);
    
    // 详细日志
    debugLog('User Info Response', $result);
    
    if (isset($result['data'])) {
        return $result['data'];
    }
    
    return null;
}

/**
 * 获取DOU+账户信息（包含昵称等）
 */
function getDouplusAccountInfo($accessToken, $advertiserId) {
    // 调用DOU+账户信息接口
    $url = 'https://ad.oceanengine.com/open_api/2/douplus/account/info/';
    $params = ['advertiser_id' => $advertiserId];
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url . '?' . http_build_query($params),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_HTTPHEADER => [
            'Access-Token: ' . $accessToken,
            'Content-Type: application/json'
        ]
    ]);
    
    $response = curl_exec($ch);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        debugLog('DOU+ Account Info Error', $error);
        return null;
    }
    
    $result = json_decode($response, true);
    debugLog('DOU+ Account Info Response', $result);
    
    if (isset($result['data'])) {
        return $result['data'];
    }
    
    return null;
}

/**
 * 获取DOU+可投放视频列表（可以获取抖音昵称）
 */
function getDouplusOptionalItems($accessToken, $advertiserId) {
    $url = 'https://ad.oceanengine.com/open_api/2/douplus/optional_items/list/';
    $params = [
        'advertiser_id' => $advertiserId,
        'page' => 1,
        'page_size' => 1
    ];
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url . '?' . http_build_query($params),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_HTTPHEADER => [
            'Access-Token: ' . $accessToken,
            'Content-Type: application/json'
        ]
    ]);
    
    $response = curl_exec($ch);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        debugLog('DOU+ Optional Items Error', $error);
        return null;
    }
    
    $result = json_decode($response, true);
    debugLog('DOU+ Optional Items Response', $result);
    
    // 从视频列表中获取抖音昵称
    if (isset($result['data']['list'][0])) {
        return $result['data']['list'][0];
    }
    
    return null;
}

/**
 * 获取DOU+订单列表（可以获取抖音昵称）
 */
function getDouplusOrderList($accessToken, $advertiserId) {
    $url = 'https://ad.oceanengine.com/open_api/2/douplus/order/list/';
    $params = [
        'advertiser_id' => $advertiserId,
        'page' => 1,
        'page_size' => 1
    ];
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url . '?' . http_build_query($params),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_HTTPHEADER => [
            'Access-Token: ' . $accessToken,
            'Content-Type: application/json'
        ]
    ]);
    
    $response = curl_exec($ch);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        debugLog('DOU+ Order List Error', $error);
        return null;
    }
    
    $result = json_decode($response, true);
    debugLog('DOU+ Order List Response', $result);
    
    return $result['data'] ?? null;
}

/**
 * 获取已授权账户信息（获取aweme_sec_uid）
 */
function getAuthorizedAccounts($accessToken) {
    $url = 'https://api.oceanengine.com/open_api/oauth2/advertiser/get/';
    $params = ['access_token' => $accessToken];
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url . '?' . http_build_query($params),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_SSL_VERIFYPEER => false
    ]);
    
    $response = curl_exec($ch);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        debugLog('Authorized Accounts Error', $error);
        return null;
    }
    
    $result = json_decode($response, true);
    debugLog('Authorized Accounts Response', $result);
    
    // 查找PLATFORM_ROLE_AWEME类型的账户，获取aweme_sec_uid
    if (isset($result['data']['list']) && is_array($result['data']['list'])) {
        foreach ($result['data']['list'] as $account) {
            if (($account['account_role'] ?? '') === 'PLATFORM_ROLE_AWEME') {
                return [
                    'aweme_sec_uid' => $account['account_string_id'] ?? '',
                    'account_name' => $account['account_name'] ?? '',
                    'advertiser_name' => $account['advertiser_name'] ?? ''
                ];
            }
        }
    }
    
    return null;
}

/**
 * 保存账号到数据库
 */
function saveAccount($userId, $tokenData, $nickname, $avatar, $advertiserId, $awemeSecUid = '') {
    $pdo = getDB();
    
    $accessToken = $tokenData['access_token'];
    $refreshToken = $tokenData['refresh_token'] ?? '';
    $expiresIn = $tokenData['expires_in'] ?? 86400;
    
    // 检查账号是否已存在
    $stmt = $pdo->prepare('SELECT id FROM douyin_account WHERE advertiser_id = ? AND deleted = 0');
    $stmt->execute([$advertiserId]);
    $existing = $stmt->fetch();
    
    // Base64编码Token
    $encryptedAccessToken = base64_encode($accessToken);
    $encryptedRefreshToken = base64_encode($refreshToken);
    
    if ($existing) {
        // 更新现有账号
        $sql = 'UPDATE douyin_account SET 
                access_token = ?, 
                refresh_token = ?, 
                token_expires_at = DATE_ADD(NOW(), INTERVAL ? SECOND),
                nickname = ?,
                avatar = ?,
                aweme_sec_uid = ?,
                status = 1,
                update_time = NOW()
                WHERE id = ?';
        $stmt = $pdo->prepare($sql);
        $stmt->execute([
            $encryptedAccessToken,
            $encryptedRefreshToken,
            $expiresIn,
            $nickname,
            $avatar,
            $awemeSecUid,
            $existing['id']
        ]);
        return ['action' => 'update', 'id' => $existing['id'], 'nickname' => $nickname];
    } else {
        // 插入新账号
        $sql = 'INSERT INTO douyin_account 
                (user_id, open_id, advertiser_id, nickname, avatar, access_token, refresh_token, token_expires_at, aweme_sec_uid, status, daily_limit, create_time, update_time, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, DATE_ADD(NOW(), INTERVAL ? SECOND), ?, 1, 10000.00, NOW(), NOW(), 0)';
        $stmt = $pdo->prepare($sql);
        $stmt->execute([
            $userId,
            $advertiserId,
            $advertiserId,
            $nickname,
            $avatar,
            $encryptedAccessToken,
            $encryptedRefreshToken,
            $expiresIn,
            $awemeSecUid
        ]);
        return ['action' => 'insert', 'id' => $pdo->lastInsertId(), 'nickname' => $nickname];
    }
}

/**
 * 记录操作日志
 */
function logOperation($userId, $action, $content) {
    try {
        $pdo = getDB();
        $sql = 'INSERT INTO operation_log (user_id, module, action, content, ip, create_time) VALUES (?, ?, ?, ?, ?, NOW())';
        $stmt = $pdo->prepare($sql);
        $stmt->execute([
            $userId,
            'account',
            $action,
            $content,
            $_SERVER['REMOTE_ADDR'] ?? ''
        ]);
    } catch (Exception $e) {
        // 日志失败不影响主流程
    }
}

// ============ 主流程 ============

$error = null;
$success = false;
$message = '';
$accountName = '';

try {
    debugLog('OAuth Callback Started', ['GET' => $_GET]);
    
    // 获取回调参数
    $authCode = $_GET['auth_code'] ?? '';
    $state = $_GET['state'] ?? '';
    
    if (empty($authCode)) {
        throw new Exception('授权码为空，请重新授权');
    }
    
    // 解析state获取用户ID
    $stateParts = explode('_', $state);
    $userId = intval($stateParts[0] ?? 1);
    if ($userId <= 0) $userId = 1;
    
    // 1. 用授权码换取access_token
    $tokenData = getAccessToken($authCode);
    
    // 2. 获取用户信息
    $userInfo = null;
    $advertiserInfo = null;
    $douplusInfo = null;
    $nickname = '';
    $avatar = '';
    
    // 从tokenData中获取advertiser_id
    $advertiserId = '';
    if (!empty($tokenData['advertiser_id'])) {
        $advertiserId = $tokenData['advertiser_id'];
    } elseif (!empty($tokenData['advertiser_ids']) && is_array($tokenData['advertiser_ids'])) {
        $advertiserId = $tokenData['advertiser_ids'][0];
    }
    
    debugLog('Advertiser ID', $advertiserId);
    
    // 尝试从tokenData中直接获取昵称
    if (!empty($tokenData['advertiser_name'])) {
        $nickname = $tokenData['advertiser_name'];
        debugLog('Got nickname from tokenData', $nickname);
    }
    
    // 尝试获取用户信息
    if (empty($nickname)) {
        try {
            $userInfo = getUserInfo($tokenData['access_token']);
            if ($userInfo) {
                $nickname = $userInfo['display_name'] ?? $userInfo['name'] ?? $userInfo['nick_name'] ?? $userInfo['nickname'] ?? '';
                $avatar = $userInfo['avatar'] ?? $userInfo['avatar_url'] ?? '';
                debugLog('Got nickname from userInfo', $nickname);
            }
        } catch (Exception $e) {
            debugLog('Get user info error', $e->getMessage());
        }
    }
    
    // 尝试获取DOU+账户信息
    if (empty($nickname) && !empty($advertiserId)) {
        try {
            $douplusInfo = getDouplusAccountInfo($tokenData['access_token'], $advertiserId);
            if ($douplusInfo) {
                $nickname = $douplusInfo['nickname'] ?? $douplusInfo['nick_name'] ?? $douplusInfo['name'] ?? $douplusInfo['aweme_nick'] ?? '';
                $avatar = $douplusInfo['avatar'] ?? $douplusInfo['avatar_url'] ?? $douplusInfo['aweme_avatar'] ?? $avatar;
                if (!empty($nickname)) {
                    debugLog('Got nickname from douplusInfo', $nickname);
                }
            }
        } catch (Exception $e) {
            debugLog('Get douplus account info error', $e->getMessage());
        }
    }
    
    // 尝试从DOU+可投放视频列表获取昵称
    if (empty($nickname) && !empty($advertiserId)) {
        try {
            $itemInfo = getDouplusOptionalItems($tokenData['access_token'], $advertiserId);
            if ($itemInfo) {
                $nickname = $itemInfo['aweme_nick'] ?? $itemInfo['nickname'] ?? $itemInfo['nick_name'] ?? '';
                $avatar = $itemInfo['aweme_avatar'] ?? $itemInfo['avatar'] ?? $avatar;
                if (!empty($nickname)) {
                    debugLog('Got nickname from optional items', $nickname);
                }
            }
        } catch (Exception $e) {
            debugLog('Get optional items error', $e->getMessage());
        }
    }
    
    // 尝试从DOU+订单列表获取昵称
    if (empty($nickname) && !empty($advertiserId)) {
        try {
            $orderInfo = getDouplusOrderList($tokenData['access_token'], $advertiserId);
            if ($orderInfo && isset($orderInfo['list'][0])) {
                $order = $orderInfo['list'][0];
                $nickname = $order['aweme_nick'] ?? $order['nickname'] ?? '';
                $avatar = $order['aweme_avatar'] ?? $order['avatar'] ?? $avatar;
                if (!empty($nickname)) {
                    debugLog('Got nickname from order list', $nickname);
                }
            }
        } catch (Exception $e) {
            debugLog('Get order list error', $e->getMessage());
        }
    }
    
    // 尝试获取广告主信息
    if (!empty($advertiserId)) {
        try {
            $advertiserInfo = getAdvertiserInfo($tokenData['access_token'], $advertiserId);
            if ($advertiserInfo) {
                // 使用广告主名称作为备用
                if (empty($nickname)) {
                    $nickname = $advertiserInfo['name'] ?? '';
                    debugLog('Got nickname from advertiserInfo', $nickname);
                }
                if (empty($avatar)) {
                    $avatar = $advertiserInfo['avatar'] ?? '';
                }
            }
        } catch (Exception $e) {
            debugLog('Get advertiser info error', $e->getMessage());
        }
    }
    
    // 如果还是没有昵称，使用默认值
    if (empty($nickname)) {
        $nickname = '用户' . substr($advertiserId, -10);
        debugLog('Using default nickname', $nickname);
    }
    
    debugLog('Final nickname and avatar', ['nickname' => $nickname, 'avatar' => $avatar]);
    
    // 获取aweme_sec_uid和真实昵称（优先使用这里的昵称）
    $awemeSecUid = '';
    try {
        $authorizedAccounts = getAuthorizedAccounts($tokenData['access_token']);
        if ($authorizedAccounts && !empty($authorizedAccounts['aweme_sec_uid'])) {
            $awemeSecUid = $authorizedAccounts['aweme_sec_uid'];
            debugLog('Got aweme_sec_uid', $awemeSecUid);
            
            // 优先使用account_name作为昵称（这是真实的抖音昵称）
            if (!empty($authorizedAccounts['account_name'])) {
                $nickname = $authorizedAccounts['account_name'];
                debugLog('Got real nickname from authorized accounts', $nickname);
            }
        }
    } catch (Exception $e) {
        debugLog('Get authorized accounts error', $e->getMessage());
    }
    
    // 如果还是没有真实昵称，尝试使用新版user/info接口
    if (empty($nickname) || strpos($nickname, '用户') === 0) {
        try {
            $userInfoV2 = getUserInfoV2($tokenData['access_token']);
            if ($userInfoV2 && !empty($userInfoV2['display_name'])) {
                $nickname = $userInfoV2['display_name'];
                debugLog('Got nickname from user/info V2', $nickname);
            }
        } catch (Exception $e) {
            debugLog('Get user info V2 error', $e->getMessage());
        }
    }
    
    debugLog('Final resolved nickname', $nickname);
    
    // 3. 保存到数据库
    $result = saveAccount($userId, $tokenData, $nickname, $avatar, $advertiserId, $awemeSecUid);
    
    $accountName = $result['nickname'];
    $action = $result['action'] === 'insert' ? '新增' : '更新';
    
    // 4. 记录日志
    logOperation($userId, 'oauth_bindAccount', "{$action}抖音账号: {$accountName}");
    
    $success = true;
    $message = "授权成功！账号「{$accountName}」已{$action}绑定。";
    
    debugLog('OAuth Callback Success', ['accountName' => $accountName, 'action' => $action]);
    
} catch (Exception $e) {
    $error = $e->getMessage();
    $message = $error;
    debugLog('OAuth Callback Error', $error);
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo $success ? '授权成功' : '授权失败'; ?> - DOU+投放管理系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 60px 50px;
            text-align: center;
            max-width: 480px;
            width: 100%;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }
        .icon {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 30px;
            font-size: 50px;
        }
        .icon.success {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
        }
        .icon.error {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
        }
        h1 { font-size: 28px; color: #1f2937; margin-bottom: 15px; }
        .message {
            font-size: 16px;
            color: #6b7280;
            line-height: 1.6;
            margin-bottom: 40px;
        }
        .account-name {
            display: inline-block;
            background: #f3f4f6;
            padding: 8px 20px;
            border-radius: 20px;
            color: #374151;
            font-weight: 600;
            margin-bottom: 30px;
        }
        .btn {
            display: inline-block;
            padding: 14px 40px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            cursor: pointer;
            border: none;
        }
        .btn-primary {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px -10px rgba(59, 130, 246, 0.5);
        }
        .btn-secondary {
            background: #f3f4f6;
            color: #374151;
            margin-left: 15px;
        }
        .btn-secondary:hover { background: #e5e7eb; }
        .countdown {
            margin-top: 30px;
            font-size: 14px;
            color: #9ca3af;
        }
        .error-detail {
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
            text-align: left;
            font-size: 13px;
            color: #991b1b;
            word-break: break-all;
        }
    </style>
</head>
<body>
    <div class="container">
        <?php if ($success): ?>
            <div class="icon success">✓</div>
            <h1>授权成功</h1>
            <?php if ($accountName): ?>
                <div class="account-name">🎵 <?php echo htmlspecialchars($accountName); ?></div>
            <?php endif; ?>
            <p class="message"><?php echo htmlspecialchars($message); ?><br>您现在可以关闭此页面，返回系统查看。</p>
            <div>
                <a href="https://douplus.easymai.cn/account/dashboard" class="btn btn-primary">返回账号管理</a>
                <button onclick="window.close()" class="btn btn-secondary">关闭页面</button>
            </div>
            <p class="countdown">页面将在 <span id="countdown">5</span> 秒后自动跳转...</p>
            <script>
                let seconds = 5;
                const countdownEl = document.getElementById('countdown');
                const timer = setInterval(() => {
                    seconds--;
                    countdownEl.textContent = seconds;
                    if (seconds <= 0) {
                        clearInterval(timer);
                        window.location.href = 'https://douplus.easymai.cn/account/dashboard';
                    }
                }, 1000);
            </script>
        <?php else: ?>
            <div class="icon error">✕</div>
            <h1>授权失败</h1>
            <p class="message">抱歉，授权过程中出现了问题，请重试。</p>
            <div class="error-detail">
                <strong>错误信息：</strong><br>
                <?php echo htmlspecialchars($error); ?>
            </div>
            <div>
                <a href="https://douplus.easymai.cn/account/dashboard" class="btn btn-primary">返回重试</a>
                <button onclick="window.close()" class="btn btn-secondary">关闭页面</button>
            </div>
        <?php endif; ?>
    </div>
</body>
</html>
