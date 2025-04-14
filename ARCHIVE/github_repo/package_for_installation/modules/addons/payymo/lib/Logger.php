<?php
/**
 * GoCardless Open Banking Logger
 *
 * @copyright Copyright (c) 2023
 * @license https://opensource.org/licenses/MIT MIT License
 */

namespace GoCardlessOpenBanking;

if (!defined("WHMCS")) {
    die("This file cannot be accessed directly");
}

use WHMCS\Database\Capsule;

/**
 * Logger Class for GoCardless Open Banking
 */
class Logger {
    /**
     * Log levels
     */
    const LEVEL_DEBUG = 'debug';
    const LEVEL_INFO = 'info';
    const LEVEL_WARNING = 'warning';
    const LEVEL_ERROR = 'error';
    
    /**
     * Log a debug message
     *
     * @param string $message Log message
     * @param array $context Additional context data
     * @return boolean Success indicator
     */
    public static function debug($message, $context = []) {
        return self::log(self::LEVEL_DEBUG, $message, $context);
    }
    
    /**
     * Log an info message
     *
     * @param string $message Log message
     * @param array $context Additional context data
     * @return boolean Success indicator
     */
    public static function info($message, $context = []) {
        return self::log(self::LEVEL_INFO, $message, $context);
    }
    
    /**
     * Log a warning message
     *
     * @param string $message Log message
     * @param array $context Additional context data
     * @return boolean Success indicator
     */
    public static function warning($message, $context = []) {
        return self::log(self::LEVEL_WARNING, $message, $context);
    }
    
    /**
     * Log an error message
     *
     * @param string $message Log message
     * @param array $context Additional context data
     * @return boolean Success indicator
     */
    public static function error($message, $context = []) {
        return self::log(self::LEVEL_ERROR, $message, $context);
    }
    
    /**
     * Log a message to the database
     *
     * @param string $level Log level
     * @param string $message Log message
     * @param array $context Additional context data
     * @return boolean Success indicator
     */
    protected static function log($level, $message, $context = []) {
        try {
            // Check if we should log debug messages
            if ($level === self::LEVEL_DEBUG) {
                // Get debug mode setting
                $debugMode = Capsule::table('tbladdonmodules')
                    ->where('module', 'gocardless_openbanking')
                    ->where('setting', 'debug_mode')
                    ->value('value');
                    
                if ($debugMode !== 'on') {
                    return true; // Skip debug logs if debug mode is off
                }
            }
            
            // Format context data as JSON
            $contextJson = !empty($context) ? json_encode($context) : null;
            
            // Insert log into database
            Capsule::table('mod_gocardless_logs')->insert([
                'level' => $level,
                'message' => $message,
                'context' => $contextJson,
                'created_at' => date('Y-m-d H:i:s')
            ]);
            
            // Also log to WHMCS activity log for errors
            if ($level === self::LEVEL_ERROR) {
                logActivity('GoCardless Open Banking Error: ' . $message);
            }
            
            return true;
        } catch (\Exception $e) {
            // If we can't log to our table, try to log to WHMCS activity log
            logActivity('GoCardless Open Banking Log Error: ' . $e->getMessage() . ' | Trying to log: ' . $message);
            return false;
        }
    }
    
    /**
     * Clean old logs from the database
     *
     * @param int $days Number of days to keep logs for
     * @return int Number of logs deleted
     */
    public static function cleanOldLogs($days = 30) {
        try {
            $cutoffDate = date('Y-m-d', strtotime("-$days days"));
            
            // Delete logs older than cutoff date
            $deleted = Capsule::table('mod_gocardless_logs')
                ->where('created_at', '<', $cutoffDate)
                ->delete();
                
            return $deleted;
        } catch (\Exception $e) {
            self::error('Failed to clean old logs: ' . $e->getMessage());
            return 0;
        }
    }
    
    /**
     * Get log levels for dropdowns
     *
     * @return array Log levels
     */
    public static function getLevels() {
        return [
            self::LEVEL_DEBUG => 'Debug',
            self::LEVEL_INFO => 'Info',
            self::LEVEL_WARNING => 'Warning',
            self::LEVEL_ERROR => 'Error'
        ];
    }
}
