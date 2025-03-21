<?php
/**
 * GoCardless Open Banking API Client
 *
 * @copyright Copyright (c) 2023
 * @license https://opensource.org/licenses/MIT MIT License
 */

namespace GoCardlessOpenBanking;

if (!defined("WHMCS")) {
    die("This file cannot be accessed directly");
}

use WHMCS\Database\Capsule;
use GoCardlessOpenBanking\Logger;

/**
 * GoCardless API Client Class
 */
class ApiClient {
    /**
     * @var array Module parameters
     */
    protected $moduleParams;
    
    /**
     * @var string API Key
     */
    protected $apiKey;
    
    /**
     * @var string API Secret
     */
    protected $apiSecret;
    
    /**
     * @var string API Endpoint
     */
    protected $apiEndpoint;
    
    /**
     * @var boolean Debug mode flag
     */
    protected $debugMode;

    /**
     * Constructor
     *
     * @param array $moduleParams Module parameters
     */
    public function __construct($moduleParams) {
        $this->moduleParams = $moduleParams;
        $this->apiKey = $moduleParams['api_key'];
        $this->apiSecret = $moduleParams['api_secret'];
        $this->apiEndpoint = 'https://api.gocardless.com/open-banking/';
        $this->debugMode = $moduleParams['debug_mode'] == 'on';
    }
    
    /**
     * Initiate OAuth flow for bank account connection
     *
     * @return string OAuth redirect URL or false on failure
     */
    public function initiateOAuth() {
        // Generate a random state parameter to prevent CSRF
        $state = md5(uniqid(mt_rand(), true));
        
        // Store state in session
        $_SESSION['gocardless_oauth_state'] = $state;
        
        // Redirect URL - this should be your callback handler
        $redirectUri = $this->getCallbackUrl();
        
        // Build authorization URL
        $authUrl = 'https://auth.gocardless.com/oauth/authorize';
        $params = [
            'client_id' => $this->apiKey,
            'redirect_uri' => $redirectUri,
            'response_type' => 'code',
            'scope' => 'bank_account_read transaction_read',
            'state' => $state
        ];
        
        $url = $authUrl . '?' . http_build_query($params);
        
        if ($this->debugMode) {
            Logger::debug('Initiating OAuth flow', [
                'redirect_uri' => $redirectUri,
                'state' => $state
            ]);
        }
        
        return $url;
    }
    
    /**
     * Process OAuth callback and exchange code for token
     *
     * @param string $code Authorization code
     * @param string $state State parameter
     * @return array Account information or error message
     */
    public function processOAuthCallback($code, $state) {
        // Verify state to prevent CSRF
        if (!isset($_SESSION['gocardless_oauth_state']) || $_SESSION['gocardless_oauth_state'] !== $state) {
            Logger::error('OAuth state mismatch', [
                'received' => $state,
                'stored' => $_SESSION['gocardless_oauth_state'] ?? 'not set'
            ]);
            return ['error' => 'Invalid state parameter'];
        }
        
        // Exchange code for token
        $tokenUrl = 'https://auth.gocardless.com/oauth/token';
        $redirectUri = $this->getCallbackUrl();
        
        $postData = [
            'client_id' => $this->apiKey,
            'client_secret' => $this->apiSecret,
            'grant_type' => 'authorization_code',
            'code' => $code,
            'redirect_uri' => $redirectUri
        ];
        
        $response = $this->sendRequest($tokenUrl, 'POST', $postData);
        
        if (isset($response['error'])) {
            Logger::error('OAuth token exchange failed', $response);
            return $response;
        }
        
        if (!isset($response['access_token'])) {
            Logger::error('OAuth token exchange response missing access_token', $response);
            return ['error' => 'Invalid response from token endpoint'];
        }
        
        // Get bank account information
        $accountInfo = $this->getBankAccountInfo($response['access_token']);
        
        if (isset($accountInfo['error'])) {
            return $accountInfo;
        }
        
        // Save account information
        try {
            Capsule::table('mod_gocardless_accounts')->insert([
                'account_id' => $accountInfo['account_id'],
                'bank_id' => $accountInfo['bank_id'],
                'bank_name' => $accountInfo['bank_name'],
                'account_name' => $accountInfo['account_name'],
                'currency' => $accountInfo['currency'],
                'oauth_token' => $response['access_token'],
                'token_expires' => date('Y-m-d H:i:s', time() + $response['expires_in']),
                'status' => 'active',
                'created_at' => date('Y-m-d H:i:s'),
                'updated_at' => date('Y-m-d H:i:s')
            ]);
            
            Logger::info('Successfully connected bank account', [
                'bank_name' => $accountInfo['bank_name'],
                'account_id' => $accountInfo['account_id']
            ]);
            
            return [
                'success' => true,
                'account' => $accountInfo
            ];
        } catch (\Exception $e) {
            Logger::error('Failed to save bank account', [
                'error' => $e->getMessage(),
                'account_info' => $accountInfo
            ]);
            
            return ['error' => 'Failed to save bank account: ' . $e->getMessage()];
        }
    }
    
    /**
     * Get bank account information
     *
     * @param string $accessToken OAuth access token
     * @return array Account information or error
     */
    protected function getBankAccountInfo($accessToken) {
        $url = $this->apiEndpoint . 'accounts';
        $headers = [
            'Authorization: Bearer ' . $accessToken
        ];
        
        $response = $this->sendRequest($url, 'GET', null, $headers);
        
        if (isset($response['error'])) {
            Logger::error('Failed to get bank account info', $response);
            return $response;
        }
        
        if (!isset($response['accounts']) || !is_array($response['accounts']) || empty($response['accounts'])) {
            Logger::error('Invalid response from accounts endpoint', $response);
            return ['error' => 'Invalid response from accounts endpoint'];
        }
        
        $account = $response['accounts'][0];
        
        return [
            'account_id' => $account['id'],
            'bank_id' => $account['institution_id'],
            'bank_name' => $account['institution_name'],
            'account_name' => $account['name'],
            'currency' => $account['currency']
        ];
    }
    
    /**
     * Get transactions for an account
     *
     * @param string $accountId Account ID
     * @param string $accessToken OAuth access token
     * @param string $dateFrom From date (YYYY-MM-DD)
     * @param string $dateTo To date (YYYY-MM-DD)
     * @return array Transactions or error
     */
    public function getTransactions($accountId, $accessToken, $dateFrom = null, $dateTo = null) {
        if (!$dateFrom) {
            $dateFrom = date('Y-m-d', strtotime('-7 days'));
        }
        
        if (!$dateTo) {
            $dateTo = date('Y-m-d');
        }
        
        $url = $this->apiEndpoint . 'accounts/' . $accountId . '/transactions';
        $params = [
            'from_date' => $dateFrom,
            'to_date' => $dateTo
        ];
        
        $url .= '?' . http_build_query($params);
        
        $headers = [
            'Authorization: Bearer ' . $accessToken
        ];
        
        $response = $this->sendRequest($url, 'GET', null, $headers);
        
        if (isset($response['error'])) {
            Logger::error('Failed to get transactions', [
                'error' => $response['error'],
                'account_id' => $accountId
            ]);
            return $response;
        }
        
        if (!isset($response['transactions']) || !is_array($response['transactions'])) {
            Logger::error('Invalid response from transactions endpoint', $response);
            return ['error' => 'Invalid response from transactions endpoint'];
        }
        
        return $response['transactions'];
    }
    
    /**
     * Refresh OAuth token
     *
     * @param string $refreshToken Refresh token
     * @return array New tokens or error
     */
    public function refreshToken($refreshToken) {
        $tokenUrl = 'https://auth.gocardless.com/oauth/token';
        
        $postData = [
            'client_id' => $this->apiKey,
            'client_secret' => $this->apiSecret,
            'grant_type' => 'refresh_token',
            'refresh_token' => $refreshToken
        ];
        
        $response = $this->sendRequest($tokenUrl, 'POST', $postData);
        
        if (isset($response['error'])) {
            Logger::error('Failed to refresh token', $response);
            return $response;
        }
        
        if (!isset($response['access_token'])) {
            Logger::error('Invalid response from token refresh endpoint', $response);
            return ['error' => 'Invalid response from token refresh endpoint'];
        }
        
        return [
            'access_token' => $response['access_token'],
            'refresh_token' => $response['refresh_token'],
            'expires_in' => $response['expires_in']
        ];
    }
    
    /**
     * Send HTTP request to API
     *
     * @param string $url API URL
     * @param string $method HTTP method
     * @param array $data Request data
     * @param array $headers Additional headers
     * @return array Response data
     */
    protected function sendRequest($url, $method = 'GET', $data = null, $headers = []) {
        $ch = curl_init();
        
        $defaultHeaders = [
            'Content-Type: application/json',
            'Accept: application/json'
        ];
        
        $allHeaders = array_merge($defaultHeaders, $headers);
        
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $allHeaders);
        
        if ($method === 'POST') {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        } elseif ($method !== 'GET') {
            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
            if ($data) {
                curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            }
        }
        
        // Enable debug output if debug mode is enabled
        if ($this->debugMode) {
            curl_setopt($ch, CURLOPT_VERBOSE, true);
            $verbose = fopen('php://temp', 'w+');
            curl_setopt($ch, CURLOPT_STDERR, $verbose);
        }
        
        $responseBody = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        
        if ($this->debugMode) {
            rewind($verbose);
            $verboseLog = stream_get_contents($verbose);
            Logger::debug('API Request', [
                'url' => $url,
                'method' => $method,
                'response_code' => $httpCode,
                'curl_verbose' => $verboseLog
            ]);
        }
        
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($error) {
            Logger::error('CURL Error', ['error' => $error, 'url' => $url]);
            return ['error' => 'CURL Error: ' . $error];
        }
        
        $response = json_decode($responseBody, true);
        
        if ($httpCode >= 400) {
            Logger::error('API Error', [
                'code' => $httpCode,
                'response' => $response,
                'url' => $url
            ]);
            
            return [
                'error' => 'API Error: ' . ($response['error_description'] ?? $response['error'] ?? 'Unknown error'),
                'http_code' => $httpCode
            ];
        }
        
        return $response;
    }
    
    /**
     * Get OAuth callback URL
     *
     * @return string Callback URL
     */
    protected function getCallbackUrl() {
        $systemUrl = rtrim(Capsule::table('tblconfiguration')
            ->where('setting', 'SystemURL')
            ->value('value'), '/');
            
        return $systemUrl . '/modules/addons/gocardless_openbanking/callback.php';
    }
}
