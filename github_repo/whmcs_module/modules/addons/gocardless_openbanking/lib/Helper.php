<?php
/**
 * GoCardless Open Banking Helper Functions
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
use GoCardlessOpenBanking\License;

/**
 * Helper Functions Class
 */
class Helper {
    /**
     * Get module settings
     *
     * @return array Module settings
     */
    public static function getModuleSettings() {
        try {
            $settings = Capsule::table('tbladdonmodules')
                ->where('module', 'gocardless_openbanking')
                ->pluck('value', 'setting')
                ->toArray();
                
            return $settings;
        } catch (\Exception $e) {
            Logger::error('Error retrieving module settings: ' . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Update module setting
     *
     * @param string $setting Setting name
     * @param string $value Setting value
     * @return boolean Success flag
     */
    public static function updateModuleSetting($setting, $value) {
        try {
            Capsule::table('tbladdonmodules')
                ->where('module', 'gocardless_openbanking')
                ->where('setting', $setting)
                ->update(['value' => $value]);
                
            return true;
        } catch (\Exception $e) {
            Logger::error('Error updating module setting: ' . $e->getMessage(), [
                'setting' => $setting
            ]);
            return false;
        }
    }
    
    /**
     * Get the last cron run date
     *
     * @return string Last cron run date or empty string
     */
    public static function getLastCronRun() {
        try {
            $lastRun = Capsule::table('tbladminnotesdata')
                ->where('admin_notes_data_key', 'gocardless_lastcron')
                ->value('admin_notes_data_value');
                
            return $lastRun ?: '';
        } catch (\Exception $e) {
            Logger::error('Error retrieving last cron run: ' . $e->getMessage());
            return '';
        }
    }
    
    /**
     * Update the last cron run date
     *
     * @param string $date Date to set
     * @return boolean Success flag
     */
    public static function updateLastCronRun($date) {
        try {
            // Check if entry exists
            $exists = Capsule::table('tbladminnotesdata')
                ->where('admin_notes_data_key', 'gocardless_lastcron')
                ->exists();
                
            if ($exists) {
                Capsule::table('tbladminnotesdata')
                    ->where('admin_notes_data_key', 'gocardless_lastcron')
                    ->update(['admin_notes_data_value' => $date]);
            } else {
                Capsule::table('tbladminnotesdata')->insert([
                    'admin_notes_data_key' => 'gocardless_lastcron',
                    'admin_notes_data_value' => $date
                ]);
            }
            
            return true;
        } catch (\Exception $e) {
            Logger::error('Error updating last cron run: ' . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Run the cron job
     *
     * @return array Cron job result
     */
    public static function runCronJob() {
        try {
            // Get module settings
            $settings = self::getModuleSettings();
            
            // Verify license before running cron
            if (!License::verify($settings['license_key'])) {
                Logger::error('License verification failed, cron job aborted');
                return [
                    'success' => false,
                    'error' => 'License verification failed'
                ];
            }
            
            // Initialize cron job handler
            require_once __DIR__ . '/CronJob.php';
            $cronJob = new CronJob($settings);
            $result = $cronJob->run();
            
            // Update last run timestamp
            self::updateLastCronRun(date('Y-m-d H:i:s'));
            
            return $result;
        } catch (\Exception $e) {
            Logger::error('Error running cron job: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => $e->getMessage()
            ];
        }
    }
    
    /**
     * Verify the module license
     *
     * @return boolean License validity
     */
    public static function verifyLicense() {
        try {
            $settings = self::getModuleSettings();
            
            if (empty($settings['license_key'])) {
                Logger::error('No license key configured');
                return false;
            }
            
            return License::verify($settings['license_key']);
        } catch (\Exception $e) {
            Logger::error('Error verifying license: ' . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Format currency amount
     *
     * @param float $amount Amount to format
     * @param string $currency Currency code
     * @return string Formatted amount
     */
    public static function formatCurrency($amount, $currency) {
        return number_format($amount, 2) . ' ' . $currency;
    }
    
    /**
     * Format date in the system's configured format
     *
     * @param string $date Date to format
     * @return string Formatted date
     */
    public static function formatDate($date) {
        $dateFormat = Capsule::table('tblconfiguration')
            ->where('setting', 'DateFormat')
            ->value('value');
            
        if (!$dateFormat) {
            $dateFormat = 'Y-m-d';
        }
        
        $timestamp = strtotime($date);
        
        switch ($dateFormat) {
            case 'DD/MM/YYYY':
                return date('d/m/Y', $timestamp);
            case 'MM/DD/YYYY':
                return date('m/d/Y', $timestamp);
            case 'YYYY/MM/DD':
                return date('Y/m/d', $timestamp);
            case 'YYYY-MM-DD':
            default:
                return date('Y-m-d', $timestamp);
        }
    }
    
    /**
     * Format datetime in the system's configured format
     *
     * @param string $datetime Datetime to format
     * @return string Formatted datetime
     */
    public static function formatDateTime($datetime) {
        $dateFormat = Capsule::table('tblconfiguration')
            ->where('setting', 'DateFormat')
            ->value('value');
            
        if (!$dateFormat) {
            $dateFormat = 'Y-m-d';
        }
        
        $timestamp = strtotime($datetime);
        
        switch ($dateFormat) {
            case 'DD/MM/YYYY':
                return date('d/m/Y H:i', $timestamp);
            case 'MM/DD/YYYY':
                return date('m/d/Y H:i', $timestamp);
            case 'YYYY/MM/DD':
                return date('Y/m/d H:i', $timestamp);
            case 'YYYY-MM-DD':
            default:
                return date('Y-m-d H:i', $timestamp);
        }
    }
    
    /**
     * Get a list of clients for dropdown selection
     *
     * @return array Client list (id => name)
     */
    public static function getClientList() {
        try {
            $clients = Capsule::table('tblclients')
                ->select(['id', 'firstname', 'lastname', 'companyname', 'email'])
                ->orderBy('lastname')
                ->orderBy('firstname')
                ->get();
                
            $clientList = [];
            foreach ($clients as $client) {
                $name = $client->firstname . ' ' . $client->lastname;
                if ($client->companyname) {
                    $name .= ' (' . $client->companyname . ')';
                }
                $clientList[$client->id] = $name;
            }
            
            return $clientList;
        } catch (\Exception $e) {
            Logger::error('Error retrieving client list: ' . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Get client details by ID
     *
     * @param int $clientId Client ID
     * @return array Client details
     */
    public static function getClientDetails($clientId) {
        try {
            $result = localAPI('GetClientsDetails', ['clientid' => $clientId]);
            
            if ($result['result'] === 'success') {
                return $result;
            } else {
                Logger::error('Error retrieving client details', [
                    'client_id' => $clientId,
                    'error' => $result['message']
                ]);
                return null;
            }
        } catch (\Exception $e) {
            Logger::error('Exception retrieving client details: ' . $e->getMessage(), [
                'client_id' => $clientId
            ]);
            return null;
        }
    }
    
    /**
     * Get client invoices
     *
     * @param int $clientId Client ID
     * @param string $status Invoice status filter
     * @return array Client invoices
     */
    public static function getClientInvoices($clientId, $status = 'Unpaid') {
        try {
            $result = localAPI('GetInvoices', [
                'userid' => $clientId,
                'status' => $status
            ]);
            
            if ($result['result'] === 'success') {
                return $result['invoices']['invoice'];
            } else {
                Logger::error('Error retrieving client invoices', [
                    'client_id' => $clientId,
                    'error' => $result['message']
                ]);
                return [];
            }
        } catch (\Exception $e) {
            Logger::error('Exception retrieving client invoices: ' . $e->getMessage(), [
                'client_id' => $clientId
            ]);
            return [];
        }
    }
    
    /**
     * Get invoice details
     *
     * @param int $invoiceId Invoice ID
     * @return array Invoice details
     */
    public static function getInvoiceDetails($invoiceId) {
        try {
            $result = localAPI('GetInvoice', ['invoiceid' => $invoiceId]);
            
            if ($result['result'] === 'success') {
                return $result;
            } else {
                Logger::error('Error retrieving invoice details', [
                    'invoice_id' => $invoiceId,
                    'error' => $result['message']
                ]);
                return null;
            }
        } catch (\Exception $e) {
            Logger::error('Exception retrieving invoice details: ' . $e->getMessage(), [
                'invoice_id' => $invoiceId
            ]);
            return null;
        }
    }
}
