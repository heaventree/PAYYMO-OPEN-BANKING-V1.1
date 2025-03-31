<?php
/**
 * GoCardless Open Banking Database Helper
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
 * Database Helper Class
 */
class Database {
    /**
     * Get paged transactions with filtering
     *
     * @param array $filters Filter parameters
     * @param int $page Page number
     * @param int $limit Items per page
     * @return array Transactions and pagination data
     */
    public static function getTransactions($filters = [], $page = 1, $limit = 25) {
        try {
            $query = Capsule::table('mod_gocardless_transactions');
            
            // Apply filters
            if (!empty($filters['status'])) {
                $query->where('status', $filters['status']);
            }
            
            if (!empty($filters['date_from'])) {
                $query->where('transaction_date', '>=', $filters['date_from']);
            }
            
            if (!empty($filters['date_to'])) {
                $query->where('transaction_date', '<=', $filters['date_to'] . ' 23:59:59');
            }
            
            if (!empty($filters['search'])) {
                $search = $filters['search'];
                $query->where(function ($q) use ($search) {
                    $q->where('transaction_id', 'like', "%$search%")
                      ->orWhere('reference', 'like', "%$search%")
                      ->orWhere('description', 'like', "%$search%")
                      ->orWhere('account_name', 'like', "%$search%")
                      ->orWhere('bank_name', 'like', "%$search%");
                });
            }
            
            // Get total count for pagination
            $total = $query->count();
            
            // Calculate pagination
            $offset = ($page - 1) * $limit;
            $totalPages = ceil($total / $limit);
            
            // Get paginated data
            $transactions = $query->orderBy('transaction_date', 'desc')
                ->offset($offset)
                ->limit($limit)
                ->get();
                
            return [
                'transactions' => $transactions,
                'pagination' => [
                    'page' => $page,
                    'limit' => $limit,
                    'total' => $total,
                    'totalPages' => $totalPages
                ]
            ];
        } catch (\Exception $e) {
            Logger::error('Error retrieving transactions: ' . $e->getMessage());
            return [
                'error' => $e->getMessage(),
                'transactions' => [],
                'pagination' => [
                    'page' => $page,
                    'limit' => $limit,
                    'total' => 0,
                    'totalPages' => 0
                ]
            ];
        }
    }
    
    /**
     * Get paged matches with filtering
     *
     * @param array $filters Filter parameters
     * @param int $page Page number
     * @param int $limit Items per page
     * @return array Matches and pagination data
     */
    public static function getMatches($filters = [], $page = 1, $limit = 25) {
        try {
            $query = Capsule::table('mod_gocardless_matches')
                ->join('mod_gocardless_transactions', 'mod_gocardless_matches.transaction_id', '=', 'mod_gocardless_transactions.id')
                ->select([
                    'mod_gocardless_matches.*',
                    'mod_gocardless_transactions.transaction_id as transaction_ref',
                    'mod_gocardless_transactions.amount',
                    'mod_gocardless_transactions.currency',
                    'mod_gocardless_transactions.bank_name',
                    'mod_gocardless_transactions.transaction_date'
                ]);
            
            // Apply filters
            if (!empty($filters['status'])) {
                $query->where('mod_gocardless_matches.status', $filters['status']);
            }
            
            // Get total count for pagination
            $total = $query->count();
            
            // Calculate pagination
            $offset = ($page - 1) * $limit;
            $totalPages = ceil($total / $limit);
            
            // Get paginated data
            $matches = $query->orderBy('mod_gocardless_matches.created_at', 'desc')
                ->offset($offset)
                ->limit($limit)
                ->get();
                
            // Get invoice details for each match
            foreach ($matches as &$match) {
                try {
                    $invoice = localAPI('GetInvoice', ['invoiceid' => $match->invoice_id]);
                    if ($invoice['result'] == 'success') {
                        $match->invoice_number = $invoice['invoiceid'];
                        $match->invoice_total = $invoice['total'];
                        $match->client_id = $invoice['userid'];
                        $match->client_name = $invoice['client']['firstname'] . ' ' . $invoice['client']['lastname'];
                    } else {
                        $match->invoice_number = $match->invoice_id;
                        $match->invoice_total = 'N/A';
                        $match->client_id = 'N/A';
                        $match->client_name = 'Error loading client data';
                    }
                } catch (\Exception $e) {
                    $match->invoice_number = $match->invoice_id;
                    $match->invoice_total = 'Error';
                    $match->client_id = 'Error';
                    $match->client_name = 'Error loading client data';
                }
            }
                
            return [
                'matches' => $matches,
                'pagination' => [
                    'page' => $page,
                    'limit' => $limit,
                    'total' => $total,
                    'totalPages' => $totalPages
                ]
            ];
        } catch (\Exception $e) {
            Logger::error('Error retrieving matches: ' . $e->getMessage());
            return [
                'error' => $e->getMessage(),
                'matches' => [],
                'pagination' => [
                    'page' => $page,
                    'limit' => $limit,
                    'total' => 0,
                    'totalPages' => 0
                ]
            ];
        }
    }
    
    /**
     * Get paged logs with filtering
     *
     * @param array $filters Filter parameters
     * @param int $page Page number
     * @param int $limit Items per page
     * @return array Logs and pagination data
     */
    public static function getLogs($filters = [], $page = 1, $limit = 50) {
        try {
            $query = Capsule::table('mod_gocardless_logs');
            
            // Apply filters
            if (!empty($filters['level'])) {
                $query->where('level', $filters['level']);
            }
            
            if (!empty($filters['date_from'])) {
                $query->where('created_at', '>=', $filters['date_from']);
            }
            
            if (!empty($filters['date_to'])) {
                $query->where('created_at', '<=', $filters['date_to'] . ' 23:59:59');
            }
            
            if (!empty($filters['search'])) {
                $search = $filters['search'];
                $query->where('message', 'like', "%$search%");
            }
            
            // Get total count for pagination
            $total = $query->count();
            
            // Calculate pagination
            $offset = ($page - 1) * $limit;
            $totalPages = ceil($total / $limit);
            
            // Get paginated data
            $logs = $query->orderBy('created_at', 'desc')
                ->offset($offset)
                ->limit($limit)
                ->get();
                
            return [
                'logs' => $logs,
                'pagination' => [
                    'page' => $page,
                    'limit' => $limit,
                    'total' => $total,
                    'totalPages' => $totalPages
                ]
            ];
        } catch (\Exception $e) {
            Logger::error('Error retrieving logs: ' . $e->getMessage());
            return [
                'error' => $e->getMessage(),
                'logs' => [],
                'pagination' => [
                    'page' => $page,
                    'limit' => $limit,
                    'total' => 0,
                    'totalPages' => 0
                ]
            ];
        }
    }
    
    /**
     * Get bank accounts
     *
     * @param string $status Filter by status
     * @return array Bank accounts
     */
    public static function getBankAccounts($status = 'active') {
        try {
            $query = Capsule::table('mod_gocardless_accounts');
            
            if ($status) {
                $query->where('status', $status);
            }
            
            return $query->orderBy('bank_name', 'asc')->get();
        } catch (\Exception $e) {
            Logger::error('Error retrieving bank accounts: ' . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Get dashboard statistics
     *
     * @return array Dashboard statistics
     */
    public static function getDashboardStats() {
        try {
            // Get today's transaction total
            $today = date('Y-m-d');
            $todayTotal = Capsule::table('mod_gocardless_transactions')
                ->whereDate('transaction_date', $today)
                ->sum('amount');
                
            // Get pending matches count
            $pendingMatches = Capsule::table('mod_gocardless_matches')
                ->where('status', 'pending')
                ->count();
                
            // Get matched vs unmatched stats
            $matched = Capsule::table('mod_gocardless_transactions')
                ->where('status', 'matched')
                ->count();
                
            $unmatched = Capsule::table('mod_gocardless_transactions')
                ->where('status', 'unmatched')
                ->count();
                
            // Get bank accounts count
            $banksCount = Capsule::table('mod_gocardless_accounts')
                ->where('status', 'active')
                ->count();
                
            // Calculate matching rate
            $total = $matched + $unmatched;
            $matchRate = $total > 0 ? round(($matched / $total) * 100) : 0;
            
            return [
                'today_total' => $todayTotal,
                'pending_matches' => $pendingMatches,
                'matched' => $matched,
                'unmatched' => $unmatched,
                'match_rate' => $matchRate,
                'banks_count' => $banksCount
            ];
        } catch (\Exception $e) {
            Logger::error('Error retrieving dashboard stats: ' . $e->getMessage());
            return [
                'today_total' => 0,
                'pending_matches' => 0,
                'matched' => 0,
                'unmatched' => 0,
                'match_rate' => 0,
                'banks_count' => 0
            ];
        }
    }
    
    /**
     * Get recent transactions
     *
     * @param int $limit Number of transactions to retrieve
     * @return array Recent transactions
     */
    public static function getRecentTransactions($limit = 5) {
        try {
            return Capsule::table('mod_gocardless_transactions')
                ->orderBy('transaction_date', 'desc')
                ->limit($limit)
                ->get();
        } catch (\Exception $e) {
            Logger::error('Error retrieving recent transactions: ' . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Get daily transaction stats for the last X days
     *
     * @param int $days Number of days to retrieve
     * @return array Daily transaction stats
     */
    public static function getDailyTransactionStats($days = 7) {
        try {
            $fromDate = date('Y-m-d', strtotime("-$days days"));
            
            return Capsule::table('mod_gocardless_transactions')
                ->selectRaw('DATE(transaction_date) as date, COUNT(*) as count, SUM(amount) as amount')
                ->where('transaction_date', '>=', $fromDate)
                ->groupBy('date')
                ->orderBy('date', 'asc')
                ->get();
        } catch (\Exception $e) {
            Logger::error('Error retrieving daily transaction stats: ' . $e->getMessage());
            return [];
        }
    }
}
