<?php
/**
 * GoCardless Open Banking Invoice Handler
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
use GoCardlessOpenBanking\Helper;

/**
 * Invoice Handler Class
 */
class Invoice {
    /**
     * Add payment to an invoice from a transaction
     *
     * @param int $invoiceId Invoice ID
     * @param object $transaction Transaction object
     * @return array Result with status
     */
    public function addPayment($invoiceId, $transaction) {
        try {
            // Get invoice details to validate
            $invoice = Helper::getInvoiceDetails($invoiceId);
            
            if (!$invoice) {
                return [
                    'success' => false,
                    'message' => 'Invoice not found'
                ];
            }
            
            // Check if invoice is already paid
            if ($invoice['status'] === 'Paid') {
                return [
                    'success' => false,
                    'message' => 'Invoice is already paid'
                ];
            }
            
            // Prepare payment parameters
            $params = [
                'invoiceid' => $invoiceId,
                'transid' => $transaction->transaction_id,
                'gateway' => 'GoCardless Open Banking',
                'amount' => $transaction->amount,
                'date' => date('Y-m-d H:i:s', strtotime($transaction->transaction_date)),
                'sendconfirmation' => true
            ];
            
            // Add payment via WHMCS API
            $result = localAPI('AddInvoicePayment', $params);
            
            if ($result['result'] === 'success') {
                Logger::info('Payment successfully applied to invoice', [
                    'invoice_id' => $invoiceId,
                    'transaction_id' => $transaction->transaction_id,
                    'amount' => $transaction->amount,
                    'currency' => $transaction->currency
                ]);
                
                return [
                    'success' => true,
                    'message' => 'Payment successfully applied'
                ];
            } else {
                Logger::error('Error applying payment to invoice', [
                    'invoice_id' => $invoiceId,
                    'transaction_id' => $transaction->transaction_id,
                    'error' => $result['message']
                ]);
                
                return [
                    'success' => false,
                    'message' => $result['message']
                ];
            }
        } catch (\Exception $e) {
            Logger::error('Exception applying payment: ' . $e->getMessage(), [
                'invoice_id' => $invoiceId,
                'transaction_id' => $transaction->transaction_id
            ]);
            
            return [
                'success' => false,
                'message' => 'Exception: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Check if a transaction amount matches an invoice amount
     *
     * @param float $transactionAmount Transaction amount
     * @param array $invoice Invoice details
     * @return array Match result with confidence
     */
    public function checkAmountMatch($transactionAmount, $invoice) {
        // Get invoice balance due
        $balanceDue = $invoice['balance'];
        
        // Exact match
        if (abs($transactionAmount - $balanceDue) < 0.01) {
            return [
                'matched' => true,
                'confidence' => 1.0,
                'reason' => 'Exact amount match'
            ];
        }
        
        // Partial payment (transaction less than invoice)
        if ($transactionAmount < $balanceDue) {
            // Calculate what percentage of the invoice this payment covers
            $percentage = ($transactionAmount / $balanceDue) * 100;
            
            // Higher confidence for common percentages
            if (abs($percentage - 50) < 1) {
                return [
                    'matched' => true,
                    'confidence' => 0.85,
                    'reason' => 'Partial payment - 50%'
                ];
            } elseif (abs($percentage - 25) < 1) {
                return [
                    'matched' => true,
                    'confidence' => 0.8,
                    'reason' => 'Partial payment - 25%'
                ];
            } elseif (abs($percentage - 75) < 1) {
                return [
                    'matched' => true,
                    'confidence' => 0.8,
                    'reason' => 'Partial payment - 75%'
                ];
            } else {
                // Generic partial payment
                $confidence = 0.7;
                return [
                    'matched' => true,
                    'confidence' => $confidence,
                    'reason' => 'Partial payment - ' . round($percentage) . '%'
                ];
            }
        }
        
        // Transaction amount slightly higher than invoice (could include fees)
        if ($transactionAmount > $balanceDue && $transactionAmount <= ($balanceDue * 1.05)) {
            return [
                'matched' => true,
                'confidence' => 0.9,
                'reason' => 'Amount slightly higher (possible fees)'
            ];
        }
        
        // Transaction much larger than invoice, likely not a match
        return [
            'matched' => false,
            'confidence' => 0.2,
            'reason' => 'Amount mismatch'
        ];
    }
    
    /**
     * Find unpaid invoices for a client
     *
     * @param int $clientId Client ID
     * @return array Unpaid invoices
     */
    public function getUnpaidInvoices($clientId) {
        try {
            return Helper::getClientInvoices($clientId, 'Unpaid');
        } catch (\Exception $e) {
            Logger::error('Error retrieving unpaid invoices: ' . $e->getMessage(), [
                'client_id' => $clientId
            ]);
            return [];
        }
    }
    
    /**
     * Find recently paid invoices for a client
     *
     * @param int $clientId Client ID
     * @param int $days Number of days to look back
     * @return array Recently paid invoices
     */
    public function getRecentlyPaidInvoices($clientId, $days = 14) {
        try {
            $result = localAPI('GetInvoices', [
                'userid' => $clientId,
                'status' => 'Paid',
                'limitstart' => 0,
                'limitnum' => 50
            ]);
            
            if ($result['result'] !== 'success') {
                return [];
            }
            
            $invoices = $result['invoices']['invoice'] ?? [];
            $recentInvoices = [];
            
            $cutoffDate = strtotime("-$days days");
            
            foreach ($invoices as $invoice) {
                $datePaid = strtotime($invoice['datepaid']);
                if ($datePaid >= $cutoffDate) {
                    $recentInvoices[] = $invoice;
                }
            }
            
            return $recentInvoices;
        } catch (\Exception $e) {
            Logger::error('Error retrieving recently paid invoices: ' . $e->getMessage(), [
                'client_id' => $clientId
            ]);
            return [];
        }
    }
    
    /**
     * Get client ID from invoice
     *
     * @param int $invoiceId Invoice ID
     * @return int Client ID or 0 if not found
     */
    public function getInvoiceClientId($invoiceId) {
        try {
            $invoice = Helper::getInvoiceDetails($invoiceId);
            
            if ($invoice && isset($invoice['userid'])) {
                return $invoice['userid'];
            }
            
            return 0;
        } catch (\Exception $e) {
            Logger::error('Error retrieving invoice client ID: ' . $e->getMessage(), [
                'invoice_id' => $invoiceId
            ]);
            return 0;
        }
    }
}
