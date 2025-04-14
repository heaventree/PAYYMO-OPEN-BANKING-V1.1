<?php
/**
 * GoCardless Open Banking Transaction Matcher
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
use GoCardlessOpenBanking\Invoice;

/**
 * Transaction Matcher Class
 */
class Matcher {
    /**
     * @var float Minimum confidence threshold for suggestions
     */
    protected $minConfidence = 0.5;
    
    /**
     * Find possible matches for a transaction
     *
     * @param int $transactionId ID of the transaction to find matches for
     * @return array Matching results
     */
    public function findMatches($transactionId) {
        try {
            // Get transaction details
            $transaction = Capsule::table('mod_gocardless_transactions')
                ->where('id', $transactionId)
                ->first();
                
            if (!$transaction) {
                Logger::error('Transaction not found for matching', ['id' => $transactionId]);
                return [
                    'matches_found' => 0,
                    'matches' => []
                ];
            }
            
            Logger::debug('Finding matches for transaction', [
                'transaction_id' => $transaction->transaction_id,
                'amount' => $transaction->amount,
                'date' => $transaction->transaction_date
            ]);
            
            // Initialize invoice service
            $invoiceService = new Invoice();
            
            // Find possible matches
            $possibleMatches = $this->findPossibleMatches($transaction);
            
            // Process each possible match
            $matches = [];
            $matchesAdded = 0;
            
            foreach ($possibleMatches as $match) {
                // Get invoice details
                $invoice = Helper::getInvoiceDetails($match['invoice_id']);
                
                if (!$invoice) {
                    continue;
                }
                
                // Check amount match
                $amountMatch = $invoiceService->checkAmountMatch($transaction->amount, $invoice);
                
                if ($amountMatch['matched']) {
                    // Combine confidence scores
                    $confidence = ($amountMatch['confidence'] + $match['confidence']) / 2;
                    
                    // Only add matches above minimum confidence
                    if ($confidence >= $this->minConfidence) {
                        // Insert match suggestion to database
                        $matchId = Capsule::table('mod_gocardless_matches')->insertGetId([
                            'transaction_id' => $transactionId,
                            'invoice_id' => $match['invoice_id'],
                            'confidence' => $confidence,
                            'match_reason' => $match['reason'] . ' & ' . $amountMatch['reason'],
                            'status' => 'pending',
                            'created_at' => date('Y-m-d H:i:s'),
                            'updated_at' => date('Y-m-d H:i:s')
                        ]);
                        
                        $matches[] = [
                            'id' => $matchId,
                            'invoice_id' => $match['invoice_id'],
                            'confidence' => $confidence,
                            'reason' => $match['reason'] . ' & ' . $amountMatch['reason']
                        ];
                        
                        $matchesAdded++;
                    }
                }
            }
            
            // Log results
            Logger::info('Transaction match results', [
                'transaction_id' => $transaction->transaction_id,
                'matches_found' => $matchesAdded
            ]);
            
            return [
                'matches_found' => $matchesAdded,
                'matches' => $matches
            ];
        } catch (\Exception $e) {
            Logger::error('Error finding matches: ' . $e->getMessage(), [
                'transaction_id' => $transactionId
            ]);
            
            return [
                'matches_found' => 0,
                'matches' => [],
                'error' => $e->getMessage()
            ];
        }
    }
    
    /**
     * Find possible matches based on transaction details
     *
     * @param object $transaction Transaction object
     * @return array Possible matches
     */
    protected function findPossibleMatches($transaction) {
        $possibleMatches = [];
        
        // 1. Match by reference number if available
        if (!empty($transaction->reference)) {
            $invoicesByReference = $this->findInvoicesByReference($transaction->reference);
            foreach ($invoicesByReference as $invoiceId) {
                $possibleMatches[] = [
                    'invoice_id' => $invoiceId,
                    'confidence' => 0.9,
                    'reason' => 'Reference number match'
                ];
            }
        }
        
        // 2. Match by amount (get recent unpaid invoices)
        $invoicesByAmount = $this->findInvoicesByAmount($transaction->amount, $transaction->currency);
        foreach ($invoicesByAmount as $invoiceId) {
            // Check if already added by reference
            $exists = false;
            foreach ($possibleMatches as $match) {
                if ($match['invoice_id'] == $invoiceId) {
                    $exists = true;
                    break;
                }
            }
            
            if (!$exists) {
                $possibleMatches[] = [
                    'invoice_id' => $invoiceId,
                    'confidence' => 0.8,
                    'reason' => 'Amount match'
                ];
            }
        }
        
        // 3. Match by description (client name or email in transaction description)
        if (!empty($transaction->description)) {
            $invoicesByDescription = $this->findInvoicesByDescription($transaction->description);
            foreach ($invoicesByDescription as $match) {
                // Check if already added
                $exists = false;
                foreach ($possibleMatches as $existingMatch) {
                    if ($existingMatch['invoice_id'] == $match['invoice_id']) {
                        $exists = true;
                        break;
                    }
                }
                
                if (!$exists) {
                    $possibleMatches[] = [
                        'invoice_id' => $match['invoice_id'],
                        'confidence' => $match['confidence'],
                        'reason' => $match['reason']
                    ];
                }
            }
        }
        
        // 4. Match by date proximity (recent invoices)
        $invoicesByDate = $this->findInvoicesByDate($transaction->transaction_date);
        foreach ($invoicesByDate as $match) {
            // Check if already added
            $exists = false;
            foreach ($possibleMatches as $existingMatch) {
                if ($existingMatch['invoice_id'] == $match['invoice_id']) {
                    $exists = true;
                    break;
                }
            }
            
            if (!$exists) {
                $possibleMatches[] = [
                    'invoice_id' => $match['invoice_id'],
                    'confidence' => $match['confidence'],
                    'reason' => $match['reason']
                ];
            }
        }
        
        return $possibleMatches;
    }
    
    /**
     * Find invoices by reference number
     *
     * @param string $reference Reference number to search for
     * @return array Invoice IDs
     */
    protected function findInvoicesByReference($reference) {
        // Clean up reference for comparison
        $reference = preg_replace('/[^a-zA-Z0-9]/', '', $reference);
        
        // Try to find invoice ID directly in reference
        if (is_numeric($reference)) {
            $invoice = Helper::getInvoiceDetails($reference);
            if ($invoice && $invoice['status'] == 'Unpaid') {
                return [$reference];
            }
        }
        
        // Handle more complex cases - e.g., references with invoice prefixes or suffixes
        // Extract numeric parts that might be invoice IDs
        preg_match_all('/\d+/', $reference, $matches);
        $potentialIds = $matches[0];
        
        $foundInvoices = [];
        foreach ($potentialIds as $potentialId) {
            $invoice = Helper::getInvoiceDetails($potentialId);
            if ($invoice && $invoice['status'] == 'Unpaid') {
                $foundInvoices[] = $potentialId;
            }
        }
        
        return $foundInvoices;
    }
    
    /**
     * Find invoices by amount
     *
     * @param float $amount Transaction amount
     * @param string $currency Transaction currency
     * @return array Invoice IDs
     */
    protected function findInvoicesByAmount($amount, $currency) {
        // Get all unpaid invoices (with limit to avoid excessive API calls)
        $result = localAPI('GetInvoices', [
            'status' => 'Unpaid',
            'limitnum' => 100
        ]);
        
        if ($result['result'] !== 'success') {
            return [];
        }
        
        // Filter invoices by amount and currency
        $matchingInvoices = [];
        
        if (isset($result['invoices']['invoice']) && is_array($result['invoices']['invoice'])) {
            foreach ($result['invoices']['invoice'] as $invoice) {
                // Check exact amount match
                if (abs($invoice['balance'] - $amount) < 0.01 && $invoice['currencycode'] == $currency) {
                    $matchingInvoices[] = $invoice['id'];
                }
            }
        }
        
        return $matchingInvoices;
    }
    
    /**
     * Find invoices by transaction description
     *
     * @param string $description Transaction description
     * @return array Matches with invoice ID, confidence and reason
     */
    protected function findInvoicesByDescription($description) {
        $matches = [];
        
        // Get all clients
        $clients = Helper::getClientList();
        
        // Check if client names are in the description
        foreach ($clients as $clientId => $clientName) {
            $clientNameParts = explode(' ', strtolower($clientName));
            $descriptionLower = strtolower($description);
            
            // Look for matches in description
            $matchFound = false;
            $wordMatches = 0;
            
            foreach ($clientNameParts as $part) {
                if (strlen($part) > 2 && strpos($descriptionLower, $part) !== false) {
                    $matchFound = true;
                    $wordMatches++;
                }
            }
            
            if ($matchFound) {
                // Calculate confidence based on how many name parts matched
                $confidence = min(0.5 + ($wordMatches * 0.1), 0.8);
                
                // Get client's unpaid invoices
                $invoices = Helper::getClientInvoices($clientId);
                foreach ($invoices as $invoice) {
                    $matches[] = [
                        'invoice_id' => $invoice['id'],
                        'confidence' => $confidence,
                        'reason' => 'Client name in description'
                    ];
                }
            }
        }
        
        return $matches;
    }
    
    /**
     * Find invoices by date proximity
     *
     * @param string $transactionDate Transaction date
     * @return array Matches with invoice ID, confidence and reason
     */
    protected function findInvoicesByDate($transactionDate) {
        $matches = [];
        
        // Get recent unpaid invoices
        $result = localAPI('GetInvoices', [
            'status' => 'Unpaid',
            'limitnum' => 50
        ]);
        
        if ($result['result'] !== 'success') {
            return [];
        }
        
        $transactionTimestamp = strtotime($transactionDate);
        
        if (isset($result['invoices']['invoice']) && is_array($result['invoices']['invoice'])) {
            foreach ($result['invoices']['invoice'] as $invoice) {
                // Calculate days difference
                $invoiceDate = $invoice['date'];
                $invoiceTimestamp = strtotime($invoiceDate);
                $daysDifference = abs(($transactionTimestamp - $invoiceTimestamp) / 86400);
                
                // Higher confidence for more recent invoices
                if ($daysDifference <= 3) {
                    $confidence = 0.7; // Same day or very recent
                } elseif ($daysDifference <= 7) {
                    $confidence = 0.6; // Within a week
                } elseif ($daysDifference <= 14) {
                    $confidence = 0.5; // Within two weeks
                } else {
                    continue; // Too old, don't include
                }
                
                $matches[] = [
                    'invoice_id' => $invoice['id'],
                    'confidence' => $confidence,
                    'reason' => 'Recent invoice (' . round($daysDifference) . ' days)'
                ];
            }
        }
        
        return $matches;
    }
    
    /**
     * Process a new invoice to find matching transactions
     *
     * @param int $invoiceId ID of the new invoice
     * @return array Matching results
     */
    public function processNewInvoice($invoiceId) {
        try {
            // Get invoice details
            $invoice = Helper::getInvoiceDetails($invoiceId);
            
            if (!$invoice) {
                Logger::error('Invoice not found for matching', ['id' => $invoiceId]);
                return [
                    'matches_found' => 0,
                    'matches' => []
                ];
            }
            
            Logger::debug('Processing new invoice for matches', [
                'invoice_id' => $invoiceId,
                'amount' => $invoice['total'],
                'currency' => $invoice['currencycode']
            ]);
            
            // Find unmatched transactions within last 30 days
            $thirtyDaysAgo = date('Y-m-d', strtotime('-30 days'));
            $transactions = Capsule::table('mod_gocardless_transactions')
                ->where('status', 'unmatched')
                ->where('transaction_date', '>=', $thirtyDaysAgo)
                ->where('amount', '>', 0) // Only consider positive transactions
                ->get();
                
            // Initialize invoice service
            $invoiceService = new Invoice();
            
            // Process each transaction for potential match
            $matches = [];
            $matchesAdded = 0;
            
            foreach ($transactions as $transaction) {
                // Check amount match
                $amountMatch = $invoiceService->checkAmountMatch($transaction->amount, $invoice);
                
                if ($amountMatch['matched']) {
                    // Calculate overall confidence
                    $confidence = $amountMatch['confidence'];
                    
                    // Adjust by date proximity
                    $daysDifference = abs((strtotime($transaction->transaction_date) - strtotime($invoice['date'])) / 86400);
                    if ($daysDifference <= 3) {
                        $confidence += 0.1;
                    } elseif ($daysDifference > 14) {
                        $confidence -= 0.1;
                    }
                    
                    // Cap confidence
                    $confidence = min(max($confidence, 0), 1);
                    
                    // Only add matches above minimum confidence
                    if ($confidence >= $this->minConfidence) {
                        // Check if match already exists
                        $matchExists = Capsule::table('mod_gocardless_matches')
                            ->where('transaction_id', $transaction->id)
                            ->where('invoice_id', $invoiceId)
                            ->exists();
                            
                        if (!$matchExists) {
                            // Insert match suggestion to database
                            $matchId = Capsule::table('mod_gocardless_matches')->insertGetId([
                                'transaction_id' => $transaction->id,
                                'invoice_id' => $invoiceId,
                                'confidence' => $confidence,
                                'match_reason' => $amountMatch['reason'] . ' (from new invoice)',
                                'status' => 'pending',
                                'created_at' => date('Y-m-d H:i:s'),
                                'updated_at' => date('Y-m-d H:i:s')
                            ]);
                            
                            $matches[] = [
                                'id' => $matchId,
                                'transaction_id' => $transaction->id,
                                'confidence' => $confidence,
                                'reason' => $amountMatch['reason'] . ' (from new invoice)'
                            ];
                            
                            $matchesAdded++;
                        }
                    }
                }
            }
            
            // Log results
            Logger::info('New invoice match results', [
                'invoice_id' => $invoiceId,
                'matches_found' => $matchesAdded
            ]);
            
            return [
                'matches_found' => $matchesAdded,
                'matches' => $matches
            ];
        } catch (\Exception $e) {
            Logger::error('Error processing new invoice: ' . $e->getMessage(), [
                'invoice_id' => $invoiceId
            ]);
            
            return [
                'matches_found' => 0,
                'matches' => [],
                'error' => $e->getMessage()
            ];
        }
    }
}
