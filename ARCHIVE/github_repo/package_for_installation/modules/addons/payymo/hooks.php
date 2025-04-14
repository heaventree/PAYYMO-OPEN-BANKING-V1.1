<?php
/**
 * GoCardless Open Banking Integration Module Hooks
 *
 * @copyright Copyright (c) 2023
 * @license https://opensource.org/licenses/MIT MIT License
 */

if (!defined("WHMCS")) {
    die("This file cannot be accessed directly");
}

require_once __DIR__ . '/lib/Logger.php';
require_once __DIR__ . '/lib/Helper.php';

use GoCardlessOpenBanking\Logger;
use GoCardlessOpenBanking\Helper;

/**
 * Add Admin Dashboard Widget
 */
add_hook('AdminHomeWidgets', 1, function() {
    return [
        'gocardless_openbanking' => [
            'title' => 'GoCardless Open Banking',
            'description' => 'Displays recent transactions and pending matches.',
            'widget' => 'gocardless_openbanking_dashboard',
            'weight' => 150,
        ],
    ];
});

/**
 * Define widget output
 */
function gocardless_openbanking_dashboard($vars) {
    $moduleLink = 'addonmodules.php?module=gocardless_openbanking';
    
    // Get recent transactions
    try {
        $transactions = WHMCS\Database\Capsule::table('mod_gocardless_transactions')
            ->orderBy('transaction_date', 'desc')
            ->limit(5)
            ->get();
            
        // Get pending matches
        $pendingMatches = WHMCS\Database\Capsule::table('mod_gocardless_matches')
            ->where('status', 'pending')
            ->count();
            
        // Get today's transaction total
        $today = date('Y-m-d');
        $todayTotal = WHMCS\Database\Capsule::table('mod_gocardless_transactions')
            ->whereDate('transaction_date', $today)
            ->sum('amount');
            
        // Get matched vs unmatched stats
        $matched = WHMCS\Database\Capsule::table('mod_gocardless_transactions')
            ->where('status', 'matched')
            ->count();
            
        $unmatched = WHMCS\Database\Capsule::table('mod_gocardless_transactions')
            ->where('status', 'unmatched')
            ->count();
    } catch (\Exception $e) {
        Logger::error('Error retrieving dashboard data: ' . $e->getMessage());
        return "Error loading widget data. Check logs for details.";
    }
    
    return <<<HTML
    <div class="widget-content-padded">
        <div class="row">
            <div class="col-sm-4 text-center">
                <h3>{$todayTotal}</h3>
                <p>Today's Transactions</p>
            </div>
            <div class="col-sm-4 text-center">
                <h3>{$pendingMatches}</h3>
                <p>Pending Matches</p>
            </div>
            <div class="col-sm-4 text-center">
                <h3>{$matched} / {$unmatched}</h3>
                <p>Matched / Unmatched</p>
            </div>
        </div>
        
        <h4>Recent Transactions</h4>
        <div class="table-responsive">
            <table class="table table-striped">
                <tr>
                    <th>Date</th>
                    <th>Amount</th>
                    <th>Bank</th>
                    <th>Status</th>
                </tr>
                
    HTML;
    
    // Add transaction rows
    $html = '';
    foreach ($transactions as $transaction) {
        $statusClass = $transaction->status == 'matched' ? 'success' : 'warning';
        $date = date('Y-m-d', strtotime($transaction->transaction_date));
        $amount = number_format($transaction->amount, 2) . ' ' . $transaction->currency;
        
        $html .= <<<HTML
        <tr>
            <td>{$date}</td>
            <td>{$amount}</td>
            <td>{$transaction->bank_name}</td>
            <td><span class="label label-{$statusClass}">{$transaction->status}</span></td>
        </tr>
        HTML;
    }
    
    // Add footer with link to full view
    $html .= <<<HTML
            </table>
        </div>
        <div class="text-right">
            <a href="{$moduleLink}&action=transactions" class="btn btn-default btn-sm">
                View All Transactions
            </a>
            <a href="{$moduleLink}&action=matches" class="btn btn-primary btn-sm">
                View Pending Matches ({$pendingMatches})
            </a>
        </div>
    </div>
    HTML;
    
    return $html;
}

/**
 * Add Admin Area Menu Item
 */
add_hook('AdminAreaHeaderOutput', 1, function() {
    return <<<HTML
    <script type="text/javascript">
        $(document).ready(function() {
            // Add menu item if not already present
            if ($('#menu li.menu-item-gocardless').length === 0) {
                $('#menu').append('<li class="menu-item-gocardless"><a href="addonmodules.php?module=gocardless_openbanking"><i class="fas fa-university"></i> GoCardless Banking</a></li>');
            }
        });
    </script>
    HTML;
});

/**
 * Add cron job task
 */
add_hook('DailyCronJob', 1, function() {
    $settings = Helper::getModuleSettings();
    
    // Check if today's cron has already run
    $lastRun = Helper::getLastCronRun();
    $today = date('Y-m-d');
    
    if ($settings['cron_frequency'] == 'daily' && $lastRun != $today) {
        Helper::runCronJob();
        Helper::updateLastCronRun($today);
    }
});

/**
 * Add hourly cron job task
 */
add_hook('HourlyCronJob', 1, function() {
    $settings = Helper::getModuleSettings();
    
    // For hourly frequency, always run
    if ($settings['cron_frequency'] == 'hourly') {
        Helper::runCronJob();
        Helper::updateLastCronRun(date('Y-m-d H:i:s'));
    }
    
    // For every 4 hours, run at hours 0, 4, 8, 12, 16, 20
    if ($settings['cron_frequency'] == 'every4hours') {
        $hour = (int)date('H');
        if ($hour % 4 == 0) {
            Helper::runCronJob();
            Helper::updateLastCronRun(date('Y-m-d H:i:s'));
        }
    }
    
    // For every 12 hours, run at hours 0 and 12
    if ($settings['cron_frequency'] == 'every12hours') {
        $hour = (int)date('H');
        if ($hour == 0 || $hour == 12) {
            Helper::runCronJob();
            Helper::updateLastCronRun(date('Y-m-d H:i:s'));
        }
    }
});

/**
 * Verify license on admin login
 */
add_hook('AdminLogin', 1, function($vars) {
    // Only check occasionally to avoid excessive API calls
    if (rand(1, 10) == 1) {
        Helper::verifyLicense();
    }
});

/**
 * Add invoice payment method hook
 */
add_hook('InvoiceCreation', 1, function($vars) {
    $invoiceId = $vars['invoiceid'];
    
    // Log new invoice creation for potential future matching
    Logger::info('New invoice created: #' . $invoiceId);
    
    // Check for any pending transactions that might match this invoice
    try {
        require_once __DIR__ . '/lib/Matcher.php';
        $matcher = new GoCardlessOpenBanking\Matcher();
        $matcher->processNewInvoice($invoiceId);
    } catch (\Exception $e) {
        Logger::error('Error processing new invoice in hook: ' . $e->getMessage());
    }
});
