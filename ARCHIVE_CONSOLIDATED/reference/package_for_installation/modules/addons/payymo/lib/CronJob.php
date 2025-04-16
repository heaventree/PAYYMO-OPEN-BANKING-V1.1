<?php
/**
 * GoCardless Open Banking Cron Job Handler
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
use GoCardlessOpenBanking\ApiClient;
use GoCardlessOpenBanking\Matcher;
use GoCardlessOpenBanking\Helper;

/**
 * Cron Job Handler Class
 */
class CronJob {
    /**
     * @var array Module parameters
     */
    protected $moduleParams;
    
    /**
     * @var ApiClient GoCardless API client
     */
    protected $apiClient;
    
    /**
     * @var Matcher Transaction matcher
     */
    protected $matcher;
    
    /**
     * Constructor
     *
     * @param array $moduleParams Module parameters
     */
    public function __construct($moduleParams) {
        $this->moduleParams = $moduleParams;
        $this->apiClient = new ApiClient($moduleParams);
        $this->matcher = new Matcher();
    }
    
    /**
     * Run the cron job
     *
     * @return array Result with statistics
     */
    public function run() {
        // Log cron start
        Logger::info('Starting GoCardless Open Banking cron job');
        
        $stats = [
            'accounts_processed' => 0,
            'transactions_retrieved' => 0,
            'transactions_new' => 0,
            'matches_found' => 0,
            'errors' => 0
        ];
        
        try {
            // Get active bank accounts
            $accounts = Capsule::table('mod_gocardless_accounts')
                ->where('status', 'active')
                ->get();
                
            foreach ($accounts as $account) {
                try {
                    $accountStats = $this->processAccount($account);
                    
                    // Merge account statistics with overall statistics
                    $stats['accounts_processed']++;
                    $stats['transactions_retrieved'] += $accountStats['transactions_retrieved'];
                    $stats['transactions_new'] += $accountStats['transactions_new'];
                    $stats['matches_found'] += $accountStats['matches_found'];
                } catch (\Exception $e) {
                    Logger::error('Error processing account: ' . $e->getMessage(), [
                        'account_id' => $account->account_id,
                        'bank_name' => $account->bank_name
                    ]);
                    
                    $stats['errors']++;
                }
            }
            
            // Log cron completion
            Logger::info('GoCardless Open Banking cron job completed', $stats);
            
            return [
                'success' => true,
                'stats' => $stats
            ];
        } catch (\Exception $e) {
            Logger::error('Cron job error: ' . $e->getMessage());
            
            return [
                'success' => false,
                'error' => $e->getMessage(),
                'stats' => $stats
            ];
        }
    }
    
    /**
     * Process a bank account
     *
     * @param object $account Bank account record
     * @return array Account processing statistics
     */
    protected function processAccount($account) {
        $stats = [
            'transactions_retrieved' => 0,
            'transactions_new' => 0,
            'matches_found' => 0
        ];
        
        // Check if token is expired and refresh if needed
        if (strtotime($account->token_expires) < time()) {
            // In a real implementation, we would refresh the token
            // For now, we'll mark the account as needing re-auth
            Capsule::table('mod_gocardless_accounts')
                ->where('id', $account->id)
                ->update([
                    'status' => 'token_expired',
                    'updated_at' => date('Y-m-d H:i:s')
                ]);
                
            Logger::warning('OAuth token expired', [
                'account_id' => $account->account_id,
                'bank_name' => $account->bank_name
            ]);
            
            return $stats;
        }
        
        // Get last transaction date for this account
        $lastTransactionDate = Capsule::table('mod_gocardless_transactions')
            ->where('account_id', $account->account_id)
            ->orderBy('transaction_date', 'desc')
            ->value('transaction_date');
            
        $fromDate = $lastTransactionDate 
            ? date('Y-m-d', strtotime($lastTransactionDate))
            : date('Y-m-d', strtotime('-30 days'));
            
        // Get transactions from API
        $transactions = $this->apiClient->getTransactions(
            $account->account_id,
            $account->oauth_token,
            $fromDate,
            date('Y-m-d')
        );
        
        if (isset($transactions['error'])) {
            throw new \Exception('Failed to retrieve transactions: ' . $transactions['error']);
        }
        
        $stats['transactions_retrieved'] = count($transactions);
        
        // Process each transaction
        foreach ($transactions as $transaction) {
            // Check if transaction already exists
            $exists = Capsule::table('mod_gocardless_transactions')
                ->where('transaction_id', $transaction['id'])
                ->exists();
                
            if ($exists) {
                continue;
            }
            
            // Insert new transaction
            $transactionId = Capsule::table('mod_gocardless_transactions')->insertGetId([
                'transaction_id' => $transaction['id'],
                'bank_name' => $account->bank_name,
                'account_id' => $account->account_id,
                'account_name' => $account->account_name,
                'amount' => $transaction['amount'],
                'currency' => $transaction['currency'],
                'description' => $transaction['description'] ?? '',
                'reference' => $transaction['reference'] ?? '',
                'transaction_date' => date('Y-m-d H:i:s', strtotime($transaction['date'])),
                'status' => 'unmatched',
                'created_at' => date('Y-m-d H:i:s'),
                'updated_at' => date('Y-m-d H:i:s')
            ]);
            
            $stats['transactions_new']++;
            
            // Try to match the transaction to an invoice
            $autoMatching = $this->moduleParams['auto_matching'] === 'on';
            if ($autoMatching) {
                $matchResult = $this->matcher->findMatches($transactionId);
                $stats['matches_found'] += $matchResult['matches_found'];
                
                // If auto-apply is enabled and we have a high-confidence match, apply it
                $autoApply = $this->moduleParams['auto_apply'] === 'on';
                $confidenceThreshold = $this->getConfidenceThreshold();
                
                if ($autoApply && !empty($matchResult['matches'])) {
                    foreach ($matchResult['matches'] as $match) {
                        if ($match['confidence'] >= $confidenceThreshold) {
                            $this->applyPayment($match['id']);
                            break;
                        }
                    }
                }
            }
        }
        
        return $stats;
    }
    
    /**
     * Apply a payment match
     *
     * @param int $matchId Match ID
     * @return boolean Success flag
     */
    protected function applyPayment($matchId) {
        try {
            // Get match details
            $match = Capsule::table('mod_gocardless_matches')
                ->where('id', $matchId)
                ->first();
                
            if (!$match) {
                Logger::error('Match not found for auto-apply', ['match_id' => $matchId]);
                return false;
            }
            
            // Get transaction details
            $transaction = Capsule::table('mod_gocardless_transactions')
                ->where('id', $match->transaction_id)
                ->first();
                
            if (!$transaction) {
                Logger::error('Transaction not found for auto-apply', [
                    'match_id' => $matchId,
                    'transaction_id' => $match->transaction_id
                ]);
                return false;
            }
            
            // Apply payment to invoice
            require_once __DIR__ . '/Invoice.php';
            $invoice = new Invoice();
            $result = $invoice->addPayment($match->invoice_id, $transaction);
            
            if ($result['success']) {
                // Update match status
                Capsule::table('mod_gocardless_matches')
                    ->where('id', $matchId)
                    ->update([
                        'status' => 'approved',
                        'updated_at' => date('Y-m-d H:i:s')
                    ]);
                    
                // Update transaction status
                Capsule::table('mod_gocardless_transactions')
                    ->where('id', $match->transaction_id)
                    ->update([
                        'status' => 'matched',
                        'invoice_id' => $match->invoice_id,
                        'updated_at' => date('Y-m-d H:i:s')
                    ]);
                    
                Logger::info('Auto-applied payment match', [
                    'match_id' => $matchId,
                    'transaction_id' => $transaction->transaction_id,
                    'invoice_id' => $match->invoice_id
                ]);
                
                return true;
            } else {
                Logger::error('Failed to auto-apply payment', [
                    'match_id' => $matchId,
                    'error' => $result['message']
                ]);
                
                return false;
            }
        } catch (\Exception $e) {
            Logger::error('Error in auto-apply payment: ' . $e->getMessage(), [
                'match_id' => $matchId
            ]);
            
            return false;
        }
    }
    
    /**
     * Get confidence threshold based on settings
     *
     * @return float Confidence threshold (0-1)
     */
    protected function getConfidenceThreshold() {
        $setting = $this->moduleParams['matching_confidence'] ?? 'medium';
        
        switch ($setting) {
            case 'low':
                return 0.6;
            case 'medium':
                return 0.75;
            case 'high':
                return 0.9;
            case 'exact':
                return 1.0;
            default:
                return 0.75;
        }
    }
}
