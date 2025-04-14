<?php
/**
 * Payymo Financial Toolbox Admin Controller
 *
 * @copyright Copyright (c) 2025
 * @license https://opensource.org/licenses/MIT MIT License
 */

namespace Payymo;

if (!defined("WHMCS")) {
    die("This file cannot be accessed directly");
}

use WHMCS\Database\Capsule;
use Payymo\Logger;
use Payymo\Helper;
use Payymo\ApiClient;
use Payymo\License;

/**
 * Admin Controller Class
 */
class Admin {
    /**
     * @var array Module parameters
     */
    protected $moduleParams;
    
    /**
     * @var string Current action
     */
    protected $action;
    
    /**
     * Dispatch the admin request
     *
     * @param array $params Module parameters
     * @return string HTML output
     */
    public function dispatch($params) {
        $this->moduleParams = $params;
        $this->action = isset($_REQUEST['action']) ? $_REQUEST['action'] : 'overview';
        
        // Verify license before any admin action
        if (!License::verify($params['license_key'])) {
            return $this->renderTemplate('license', [
                'error' => 'Invalid license key. Please update your license key in the module configuration.',
                'license_key' => $params['license_key'],
                'license_status' => 'invalid'
            ]);
        }
        
        // Handle form submissions
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            return $this->handlePostRequest();
        }
        
        // Display appropriate template based on action
        switch ($this->action) {
            case 'transactions':
                return $this->showTransactions();
            case 'matches':
                return $this->showMatches();
            case 'configuration':
                return $this->showConfiguration();
            case 'logs':
                return $this->showLogs();
            case 'license':
                return $this->showLicense();
            case 'overview':
            default:
                return $this->showOverview();
        }
    }
    
    /**
     * Show module overview dashboard
     *
     * @return string HTML output
     */
    protected function showOverview() {
        // Get dashboard statistics
        try {
            // Get recent transactions
            $transactions = Capsule::table('mod_payymo_transactions')
                ->orderBy('transaction_date', 'desc')
                ->limit(10)
                ->get();
                
            // Get pending matches
            $pendingMatches = Capsule::table('mod_payymo_matches')
                ->where('status', 'pending')
                ->limit(10)
                ->get();
                
            // Calculate daily transactions - last 7 days
            $dailyStats = Capsule::table('mod_payymo_transactions')
                ->selectRaw('DATE(transaction_date) as date, COUNT(*) as count, SUM(amount) as amount')
                ->where('transaction_date', '>=', date('Y-m-d', strtotime('-7 days')))
                ->groupBy('date')
                ->orderBy('date', 'asc')
                ->get();
                
            // Format data for chart
            $chartDates = [];
            $chartAmounts = [];
            $chartCounts = [];
            
            foreach ($dailyStats as $stat) {
                $chartDates[] = $stat->date;
                $chartAmounts[] = $stat->amount;
                $chartCounts[] = $stat->count;
            }
            
            // Get matching stats
            $matchedCount = Capsule::table('mod_payymo_transactions')
                ->where('status', 'matched')
                ->count();
                
            $unmatchedCount = Capsule::table('mod_payymo_transactions')
                ->where('status', 'unmatched')
                ->count();
                
            $totalTransactions = $matchedCount + $unmatchedCount;
            $matchPercentage = $totalTransactions > 0 ? 
                round(($matchedCount / $totalTransactions) * 100) : 0;
                
            // Get connected banks count
            $banksCount = Capsule::table('mod_payymo_accounts')
                ->where('status', 'active')
                ->count();
                
            return $this->renderTemplate('overview', [
                'transactions' => $transactions,
                'pendingMatches' => $pendingMatches,
                'chartDates' => json_encode($chartDates),
                'chartAmounts' => json_encode($chartAmounts),
                'chartCounts' => json_encode($chartCounts),
                'matchedCount' => $matchedCount,
                'unmatchedCount' => $unmatchedCount,
                'matchPercentage' => $matchPercentage,
                'banksCount' => $banksCount,
                'moduleParams' => $this->moduleParams
            ]);
        } catch (\Exception $e) {
            Logger::error('Error in admin overview: ' . $e->getMessage());
            return '<div class="alert alert-danger">Error loading dashboard data: ' . $e->getMessage() . '</div>';
        }
    }
    
    /**
     * Show transactions listing
     *
     * @return string HTML output
     */
    protected function showTransactions() {
        $page = isset($_REQUEST['page']) ? (int)$_REQUEST['page'] : 1;
        $limit = 25;
        $offset = ($page - 1) * $limit;
        
        $status = isset($_REQUEST['status']) ? $_REQUEST['status'] : '';
        $dateFrom = isset($_REQUEST['date_from']) ? $_REQUEST['date_from'] : '';
        $dateTo = isset($_REQUEST['date_to']) ? $_REQUEST['date_to'] : '';
        $search = isset($_REQUEST['search']) ? $_REQUEST['search'] : '';
        
        try {
            $query = Capsule::table('mod_payymo_transactions');
            
            // Apply filters
            if ($status) {
                $query->where('status', $status);
            }
            
            if ($dateFrom) {
                $query->where('transaction_date', '>=', $dateFrom);
            }
            
            if ($dateTo) {
                $query->where('transaction_date', '<=', $dateTo . ' 23:59:59');
            }
            
            if ($search) {
                $query->where(function ($q) use ($search) {
                    $q->where('transaction_id', 'like', "%$search%")
                      ->orWhere('reference', 'like', "%$search%")
                      ->orWhere('description', 'like', "%$search%")
                      ->orWhere('account_name', 'like', "%$search%")
                      ->orWhere('bank_name', 'like', "%$search%");
                });
            }
            
            // Get total count for pagination
            $totalRecords = $query->count();
            
            // Get paginated results
            $transactions = $query->orderBy('transaction_date', 'desc')
                ->offset($offset)
                ->limit($limit)
                ->get();
                
            // Calculate pagination
            $totalPages = ceil($totalRecords / $limit);
            
            return $this->renderTemplate('transactions', [
                'transactions' => $transactions,
                'page' => $page,
                'totalPages' => $totalPages,
                'totalRecords' => $totalRecords,
                'status' => $status,
                'dateFrom' => $dateFrom,
                'dateTo' => $dateTo,
                'search' => $search
            ]);
        } catch (\Exception $e) {
            Logger::error('Error in transactions view: ' . $e->getMessage());
            return '<div class="alert alert-danger">Error loading transactions: ' . $e->getMessage() . '</div>';
        }
    }
    
    /**
     * Show matches listing
     *
     * @return string HTML output
     */
    protected function showMatches() {
        $page = isset($_REQUEST['page']) ? (int)$_REQUEST['page'] : 1;
        $limit = 25;
        $offset = ($page - 1) * $limit;
        
        $status = isset($_REQUEST['status']) ? $_REQUEST['status'] : 'pending';
        
        try {
            $query = Capsule::table('mod_payymo_matches')
                ->join('mod_payymo_transactions', 'mod_payymo_matches.transaction_id', '=', 'mod_payymo_transactions.id')
                ->select([
                    'mod_payymo_matches.*',
                    'mod_payymo_transactions.transaction_id as transaction_ref',
                    'mod_payymo_transactions.amount',
                    'mod_payymo_transactions.currency',
                    'mod_payymo_transactions.bank_name',
                    'mod_payymo_transactions.transaction_date'
                ]);
            
            // Apply filters
            if ($status) {
                $query->where('mod_payymo_matches.status', $status);
            }
            
            // Get total count for pagination
            $totalRecords = $query->count();
            
            // Get paginated results
            $matches = $query->orderBy('mod_payymo_matches.created_at', 'desc')
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
                
            // Calculate pagination
            $totalPages = ceil($totalRecords / $limit);
            
            return $this->renderTemplate('matches', [
                'matches' => $matches,
                'page' => $page,
                'totalPages' => $totalPages,
                'totalRecords' => $totalRecords,
                'status' => $status
            ]);
        } catch (\Exception $e) {
            Logger::error('Error in matches view: ' . $e->getMessage());
            return '<div class="alert alert-danger">Error loading matches: ' . $e->getMessage() . '</div>';
        }
    }
    
    /**
     * Show module configuration
     *
     * @return string HTML output
     */
    protected function showConfiguration() {
        // Get list of connected bank accounts
        try {
            $accounts = Capsule::table('mod_payymo_accounts')
                ->orderBy('bank_name', 'asc')
                ->get();
                
            return $this->renderTemplate('configuration', [
                'accounts' => $accounts,
                'moduleParams' => $this->moduleParams
            ]);
        } catch (\Exception $e) {
            Logger::error('Error in configuration view: ' . $e->getMessage());
            return '<div class="alert alert-danger">Error loading configuration: ' . $e->getMessage() . '</div>';
        }
    }
    
    /**
     * Show logs listing
     *
     * @return string HTML output
     */
    protected function showLogs() {
        $page = isset($_REQUEST['page']) ? (int)$_REQUEST['page'] : 1;
        $limit = 50;
        $offset = ($page - 1) * $limit;
        
        $level = isset($_REQUEST['level']) ? $_REQUEST['level'] : '';
        $dateFrom = isset($_REQUEST['date_from']) ? $_REQUEST['date_from'] : '';
        $dateTo = isset($_REQUEST['date_to']) ? $_REQUEST['date_to'] : '';
        $search = isset($_REQUEST['search']) ? $_REQUEST['search'] : '';
        
        try {
            $query = Capsule::table('mod_payymo_logs');
            
            // Apply filters
            if ($level) {
                $query->where('level', $level);
            }
            
            if ($dateFrom) {
                $query->where('created_at', '>=', $dateFrom);
            }
            
            if ($dateTo) {
                $query->where('created_at', '<=', $dateTo . ' 23:59:59');
            }
            
            if ($search) {
                $query->where('message', 'like', "%$search%");
            }
            
            // Get total count for pagination
            $totalRecords = $query->count();
            
            // Get paginated results
            $logs = $query->orderBy('created_at', 'desc')
                ->offset($offset)
                ->limit($limit)
                ->get();
                
            // Calculate pagination
            $totalPages = ceil($totalRecords / $limit);
            
            return $this->renderTemplate('logs', [
                'logs' => $logs,
                'page' => $page,
                'totalPages' => $totalPages,
                'totalRecords' => $totalRecords,
                'level' => $level,
                'dateFrom' => $dateFrom,
                'dateTo' => $dateTo,
                'search' => $search
            ]);
        } catch (\Exception $e) {
            Logger::error('Error in logs view: ' . $e->getMessage());
            return '<div class="alert alert-danger">Error loading logs: ' . $e->getMessage() . '</div>';
        }
    }
    
    /**
     * Show license information
     *
     * @return string HTML output
     */
    protected function showLicense() {
        $licenseKey = $this->moduleParams['license_key'];
        $licenseStatus = License::verify($licenseKey) ? 'valid' : 'invalid';
        
        $licenseInfo = License::getInfo($licenseKey);
        
        return $this->renderTemplate('license', [
            'license_key' => $licenseKey,
            'license_status' => $licenseStatus,
            'license_info' => $licenseInfo
        ]);
    }
    
    /**
     * Handle POST form submissions
     *
     * @return string HTML output with redirect
     */
    protected function handlePostRequest() {
        $formAction = isset($_POST['form_action']) ? $_POST['form_action'] : '';
        
        switch ($formAction) {
            case 'approve_match':
                return $this->processApproveMatch();
            case 'reject_match':
                return $this->processRejectMatch();
            case 'run_cron':
                return $this->processRunCron();
            case 'add_bank':
                return $this->processAddBank();
            case 'remove_bank':
                return $this->processRemoveBank();
            case 'clear_logs':
                return $this->processClearLogs();
            default:
                return $this->showOverview();
        }
    }
    
    /**
     * Process match approval request
     *
     * @return string HTML output with redirect
     */
    protected function processApproveMatch() {
        $matchId = isset($_POST['match_id']) ? (int)$_POST['match_id'] : 0;
        
        if (!$matchId) {
            return $this->redirectWithMessage('matches', 'error', 'No match ID provided');
        }
        
        try {
            // Get match details
            $match = Capsule::table('mod_payymo_matches')
                ->where('id', $matchId)
                ->first();
                
            if (!$match) {
                return $this->redirectWithMessage('matches', 'error', 'Match not found');
            }
            
            // Get transaction details
            $transaction = Capsule::table('mod_payymo_transactions')
                ->where('id', $match->transaction_id)
                ->first();
                
            if (!$transaction) {
                return $this->redirectWithMessage('matches', 'error', 'Transaction not found');
            }
            
            // Apply payment to invoice
            require_once __DIR__ . '/Invoice.php';
            $invoice = new Invoice();
            $result = $invoice->addPayment($match->invoice_id, $transaction);
            
            if ($result['success']) {
                // Update match status
                Capsule::table('mod_payymo_matches')
                    ->where('id', $matchId)
                    ->update([
                        'status' => 'approved',
                        'updated_at' => date('Y-m-d H:i:s')
                    ]);
                    
                // Update transaction status
                Capsule::table('mod_payymo_transactions')
                    ->where('id', $match->transaction_id)
                    ->update([
                        'status' => 'matched',
                        'invoice_id' => $match->invoice_id,
                        'updated_at' => date('Y-m-d H:i:s')
                    ]);
                    
                Logger::info('Match approved and payment applied', [
                    'match_id' => $matchId,
                    'transaction_id' => $transaction->transaction_id,
                    'invoice_id' => $match->invoice_id
                ]);
                
                return $this->redirectWithMessage('matches', 'success', 'Payment successfully applied to invoice #' . $match->invoice_id);
            } else {
                return $this->redirectWithMessage('matches', 'error', 'Failed to apply payment: ' . $result['message']);
            }
        } catch (\Exception $e) {
            Logger::error('Error approving match: ' . $e->getMessage());
            return $this->redirectWithMessage('matches', 'error', 'Error approving match: ' . $e->getMessage());
        }
    }
    
    /**
     * Process match rejection request
     *
     * @return string HTML output with redirect
     */
    protected function processRejectMatch() {
        $matchId = isset($_POST['match_id']) ? (int)$_POST['match_id'] : 0;
        
        if (!$matchId) {
            return $this->redirectWithMessage('matches', 'error', 'No match ID provided');
        }
        
        try {
            // Update match status
            Capsule::table('mod_payymo_matches')
                ->where('id', $matchId)
                ->update([
                    'status' => 'rejected',
                    'updated_at' => date('Y-m-d H:i:s')
                ]);
                
            Logger::info('Match rejected', ['match_id' => $matchId]);
            
            return $this->redirectWithMessage('matches', 'success', 'Match rejected successfully');
        } catch (\Exception $e) {
            Logger::error('Error rejecting match: ' . $e->getMessage());
            return $this->redirectWithMessage('matches', 'error', 'Error rejecting match: ' . $e->getMessage());
        }
    }
    
    /**
     * Process manual cron job run request
     *
     * @return string HTML output with redirect
     */
    protected function processRunCron() {
        try {
            Helper::runCronJob();
            return $this->redirectWithMessage('overview', 'success', 'Cron job executed successfully');
        } catch (\Exception $e) {
            Logger::error('Error running cron job: ' . $e->getMessage());
            return $this->redirectWithMessage('overview', 'error', 'Error running cron job: ' . $e->getMessage());
        }
    }
    
    /**
     * Process adding new bank account
     *
     * @return string HTML output with redirect
     */
    protected function processAddBank() {
        // Redirect to GoCardless OAuth flow
        $apiClient = new ApiClient($this->moduleParams);
        $redirectUrl = $apiClient->initiateOAuth();
        
        if ($redirectUrl) {
            header('Location: ' . $redirectUrl);
            exit;
        } else {
            return $this->redirectWithMessage('configuration', 'error', 'Failed to initiate bank connection');
        }
    }
    
    /**
     * Process removing a bank account
     *
     * @return string HTML output with redirect
     */
    protected function processRemoveBank() {
        $accountId = isset($_POST['account_id']) ? $_POST['account_id'] : '';
        
        if (!$accountId) {
            return $this->redirectWithMessage('configuration', 'error', 'No account ID provided');
        }
        
        try {
            // Delete the account
            Capsule::table('mod_payymo_accounts')
                ->where('account_id', $accountId)
                ->delete();
                
            Logger::info('Bank account removed', ['account_id' => $accountId]);
            
            return $this->redirectWithMessage('configuration', 'success', 'Bank account removed successfully');
        } catch (\Exception $e) {
            Logger::error('Error removing bank account: ' . $e->getMessage());
            return $this->redirectWithMessage('configuration', 'error', 'Error removing bank account: ' . $e->getMessage());
        }
    }
    
    /**
     * Process clearing logs
     *
     * @return string HTML output with redirect
     */
    protected function processClearLogs() {
        $days = isset($_POST['days']) ? (int)$_POST['days'] : 30;
        
        try {
            $cutoffDate = date('Y-m-d', strtotime("-$days days"));
            
            // Delete logs older than cutoff date
            $deleted = Capsule::table('mod_payymo_logs')
                ->where('created_at', '<', $cutoffDate)
                ->delete();
                
            Logger::info("Cleared logs older than $days days", ['count' => $deleted]);
            
            return $this->redirectWithMessage('logs', 'success', "Successfully cleared $deleted logs older than $days days");
        } catch (\Exception $e) {
            Logger::error('Error clearing logs: ' . $e->getMessage());
            return $this->redirectWithMessage('logs', 'error', 'Error clearing logs: ' . $e->getMessage());
        }
    }
    
    /**
     * Render a template with variables
     *
     * @param string $template Template name
     * @param array $vars Template variables
     * @return string Rendered HTML
     */
    protected function renderTemplate($template, $vars = []) {
        $templatePath = __DIR__ . '/../templates/admin/' . $template . '.tpl';
        
        if (!file_exists($templatePath)) {
            return "Template not found: $template";
        }
        
        // Add module params to template vars
        $vars['moduleParams'] = $this->moduleParams;
        $vars['moduleLink'] = $this->moduleParams['modulelink'];
        
        // Extract vars to make them available in the template
        extract($vars);
        
        // Start output buffering
        ob_start();
        include $templatePath;
        $content = ob_get_clean();
        
        return $content;
    }
    
    /**
     * Redirect with a message
     *
     * @param string $action Action to redirect to
     * @param string $type Message type (success/error)
     * @param string $message The message to display
     * @return string HTML output with redirect script
     */
    protected function redirectWithMessage($action, $type, $message) {
        $url = $this->moduleParams['modulelink'] . '&action=' . $action;
        
        $messageHtml = '';
        if ($type == 'success') {
            $messageHtml = '<div class="alert alert-success">' . $message . '</div>';
        } else {
            $messageHtml = '<div class="alert alert-danger">' . $message . '</div>';
        }
        
        // Store message in session
        $_SESSION['payymo_message'] = $messageHtml;
        
        // Return redirect script
        return <<<HTML
        <script>
            window.location.href = "{$url}";
        </script>
        <p>If you are not redirected automatically, please <a href="{$url}">click here</a>.</p>
        HTML;
    }
}
