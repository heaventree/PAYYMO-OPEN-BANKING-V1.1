<?php
/**
 * GoCardless Open Banking License Verification
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
 * License Verification Class
 */
class License {
    /**
     * @var string API endpoint for license verification
     */
    protected static $apiEndpoint = 'https://api.example.com/license/verify';
    
    /**
     * @var int Cache duration in seconds
     */
    protected static $cacheDuration = 86400; // 24 hours
    
    /**
     * Verify license key
     *
     * @param string $licenseKey License key to verify
     * @return boolean License validity
     */
    public static function verify($licenseKey) {
        if (empty($licenseKey)) {
            Logger::error('License key is empty');
            return false;
        }
        
        // Check cached result first
        $cachedResult = self::getCachedVerification($licenseKey);
        if ($cachedResult !== null) {
            return $cachedResult;
        }
        
        // Get system information for verification
        $systemInfo = self::getSystemInfo();
        
        // Verify license with API
        $result = self::verifyWithApi($licenseKey, $systemInfo);
        
        // Cache result
        self::cacheVerificationResult($licenseKey, $result);
        
        return $result;
    }
    
    /**
     * Get license information
     *
     * @param string $licenseKey License key
     * @return array License information
     */
    public static function getInfo($licenseKey) {
        if (empty($licenseKey)) {
            return [
                'status' => 'invalid',
                'expires' => 'N/A',
                'registered_to' => 'N/A',
                'features' => []
            ];
        }
        
        // Get cached license info
        $cachedInfo = self::getCachedLicenseInfo($licenseKey);
        if ($cachedInfo !== null) {
            return $cachedInfo;
        }
        
        // Get system information for verification
        $systemInfo = self::getSystemInfo();
        
        // Get license info from API
        $info = self::getLicenseInfoFromApi($licenseKey, $systemInfo);
        
        // Cache license info
        self::cacheLicenseInfo($licenseKey, $info);
        
        return $info;
    }
    
    /**
     * Get cached verification result
     *
     * @param string $licenseKey License key
     * @return boolean|null Cached result or null if not cached
     */
    protected static function getCachedVerification($licenseKey) {
        try {
            $cacheKey = 'license_verification_' . md5($licenseKey);
            
            $cachedData = Capsule::table('tbladminnotesdata')
                ->where('admin_notes_data_key', $cacheKey)
                ->first();
                
            if (!$cachedData) {
                return null;
            }
            
            // Check if cache is expired
            $cacheData = json_decode($cachedData->admin_notes_data_value, true);
            if (!isset($cacheData['timestamp']) || (time() - $cacheData['timestamp'] > self::$cacheDuration)) {
                return null;
            }
            
            return $cacheData['result'];
        } catch (\Exception $e) {
            Logger::error('Error retrieving cached license verification: ' . $e->getMessage());
            return null;
        }
    }
    
    /**
     * Cache verification result
     *
     * @param string $licenseKey License key
     * @param boolean $result Verification result
     * @return void
     */
    protected static function cacheVerificationResult($licenseKey, $result) {
        try {
            $cacheKey = 'license_verification_' . md5($licenseKey);
            
            $cacheData = [
                'timestamp' => time(),
                'result' => $result
            ];
            
            // Check if cache entry exists
            $exists = Capsule::table('tbladminnotesdata')
                ->where('admin_notes_data_key', $cacheKey)
                ->exists();
                
            if ($exists) {
                Capsule::table('tbladminnotesdata')
                    ->where('admin_notes_data_key', $cacheKey)
                    ->update(['admin_notes_data_value' => json_encode($cacheData)]);
            } else {
                Capsule::table('tbladminnotesdata')->insert([
                    'admin_notes_data_key' => $cacheKey,
                    'admin_notes_data_value' => json_encode($cacheData)
                ]);
            }
        } catch (\Exception $e) {
            Logger::error('Error caching license verification: ' . $e->getMessage());
        }
    }
    
    /**
     * Get cached license information
     *
     * @param string $licenseKey License key
     * @return array|null Cached license info or null if not cached
     */
    protected static function getCachedLicenseInfo($licenseKey) {
        try {
            $cacheKey = 'license_info_' . md5($licenseKey);
            
            $cachedData = Capsule::table('tbladminnotesdata')
                ->where('admin_notes_data_key', $cacheKey)
                ->first();
                
            if (!$cachedData) {
                return null;
            }
            
            // Check if cache is expired
            $cacheData = json_decode($cachedData->admin_notes_data_value, true);
            if (!isset($cacheData['timestamp']) || (time() - $cacheData['timestamp'] > self::$cacheDuration)) {
                return null;
            }
            
            return $cacheData['info'];
        } catch (\Exception $e) {
            Logger::error('Error retrieving cached license info: ' . $e->getMessage());
            return null;
        }
    }
    
    /**
     * Cache license information
     *
     * @param string $licenseKey License key
     * @param array $info License information
     * @return void
     */
    protected static function cacheLicenseInfo($licenseKey, $info) {
        try {
            $cacheKey = 'license_info_' . md5($licenseKey);
            
            $cacheData = [
                'timestamp' => time(),
                'info' => $info
            ];
            
            // Check if cache entry exists
            $exists = Capsule::table('tbladminnotesdata')
                ->where('admin_notes_data_key', $cacheKey)
                ->exists();
                
            if ($exists) {
                Capsule::table('tbladminnotesdata')
                    ->where('admin_notes_data_key', $cacheKey)
                    ->update(['admin_notes_data_value' => json_encode($cacheData)]);
            } else {
                Capsule::table('tbladminnotesdata')->insert([
                    'admin_notes_data_key' => $cacheKey,
                    'admin_notes_data_value' => json_encode($cacheData)
                ]);
            }
        } catch (\Exception $e) {
            Logger::error('Error caching license info: ' . $e->getMessage());
        }
    }
    
    /**
     * Get system information for license verification
     *
     * @return array System information
     */
    protected static function getSystemInfo() {
        try {
            // Get system URL
            $systemUrl = Capsule::table('tblconfiguration')
                ->where('setting', 'SystemURL')
                ->value('value');
                
            // Get company name
            $companyName = Capsule::table('tblconfiguration')
                ->where('setting', 'CompanyName')
                ->value('value');
                
            return [
                'domain' => preg_replace('#^https?://#', '', rtrim($systemUrl, '/')),
                'company_name' => $companyName,
                'ip' => $_SERVER['SERVER_ADDR'] ?? '',
                'php_version' => PHP_VERSION,
                'whmcs_version' => Capsule::table('tblconfiguration')
                    ->where('setting', 'Version')
                    ->value('value')
            ];
        } catch (\Exception $e) {
            Logger::error('Error retrieving system info: ' . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Verify license with API
     *
     * @param string $licenseKey License key
     * @param array $systemInfo System information
     * @return boolean License validity
     */
    protected static function verifyWithApi($licenseKey, $systemInfo) {
        try {
            // In a real implementation, this would make an API call to the licensing server
            // For this implementation, we'll simulate a successful verification if license is not empty
            
            // Simulate API call
            // $apiUrl = self::$apiEndpoint;
            // $postData = [
            //     'license_key' => $licenseKey,
            //     'system_info' => $systemInfo
            // ];
            
            // $ch = curl_init();
            // curl_setopt($ch, CURLOPT_URL, $apiUrl);
            // curl_setopt($ch, CURLOPT_POST, 1);
            // curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($postData));
            // curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            // curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
            // $response = curl_exec($ch);
            // curl_close($ch);
            
            // $result = json_decode($response, true);
            // if (isset($result['valid']) && $result['valid']) {
            //     return true;
            // }
            
            // Simulated implementation
            if (!empty($licenseKey) && strlen($licenseKey) >= 10) {
                return true;
            }
            
            return false;
        } catch (\Exception $e) {
            Logger::error('Error verifying license with API: ' . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Get license information from API
     *
     * @param string $licenseKey License key
     * @param array $systemInfo System information
     * @return array License information
     */
    protected static function getLicenseInfoFromApi($licenseKey, $systemInfo) {
        try {
            // In a real implementation, this would make an API call to the licensing server
            // For this implementation, we'll simulate license information
            
            // Simulate license info
            if (!empty($licenseKey) && strlen($licenseKey) >= 10) {
                return [
                    'status' => 'valid',
                    'expires' => date('Y-m-d', strtotime('+1 year')),
                    'registered_to' => $systemInfo['company_name'] ?? 'Unknown',
                    'features' => [
                        'automatic_matching' => true,
                        'partial_payments' => true,
                        'bank_connections' => 'unlimited'
                    ]
                ];
            }
            
            return [
                'status' => 'invalid',
                'expires' => 'N/A',
                'registered_to' => 'N/A',
                'features' => []
            ];
        } catch (\Exception $e) {
            Logger::error('Error getting license info from API: ' . $e->getMessage());
            
            return [
                'status' => 'error',
                'expires' => 'N/A',
                'registered_to' => 'N/A',
                'features' => [],
                'error' => $e->getMessage()
            ];
        }
    }
}
