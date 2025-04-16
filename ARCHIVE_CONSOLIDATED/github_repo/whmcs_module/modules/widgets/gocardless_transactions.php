<?php
/**
 * GoCardless Open Banking Transactions Widget
 *
 * @copyright Copyright (c) 2023
 * @license https://opensource.org/licenses/MIT MIT License
 */

namespace WHMCS\Module\Widget;

use WHMCS\Database\Capsule;
use WHMCS\Module\AbstractWidget;

/**
 * GoCardless Transactions Widget
 */
class GoCardlessTransactions extends AbstractWidget
{
    /**
     * Widget title
     *
     * @return string
     */
    protected $title = 'GoCardless Open Banking Transactions';

    /**
     * Widget description
     *
     * @return string
     */
    protected $description = 'Displays recent GoCardless Open Banking transactions and matches';

    /**
     * Widget cache lifetime
     *
     * @return int
     */
    protected $cacheExpiry = 300; // 5 minutes

    /**
     * Widget default settings
     *
     * @return array
     */
    protected $defaultSettings = [
        'title' => 'GoCardless Transactions',
        'numitems' => 5,
        'cacheExpiry' => 300,
        'showOnlyPending' => true,
    ];

    /**
     * Fetch data to display
     *
     * @return array
     */
    public function getData()
    {
        // Check if table exists
        if (!Capsule::schema()->hasTable('mod_gocardless_transactions')) {
            return [
                'error' => 'GoCardless Open Banking module not activated'
            ];
        }

        // Get widget settings
        $numItems = $this->getRouteSetting('numitems', 5);
        $showOnlyPending = $this->getRouteSetting('showOnlyPending', true);

        try {
            // Get recent transactions
            $transactionsQuery = Capsule::table('mod_gocardless_transactions')
                ->orderBy('transaction_date', 'desc')
                ->limit($numItems);

            $transactions = $transactionsQuery->get();

            // Get pending matches
            $matchesQuery = Capsule::table('mod_gocardless_matches')
                ->where('status', 'pending')
                ->join('mod_gocardless_transactions', 'mod_gocardless_matches.transaction_id', '=', 'mod_gocardless_transactions.id')
                ->select([
                    'mod_gocardless_matches.*',
                    'mod_gocardless_transactions.transaction_id as transaction_ref',
                    'mod_gocardless_transactions.amount',
                    'mod_gocardless_transactions.currency',
                    'mod_gocardless_transactions.bank_name',
                    'mod_gocardless_transactions.transaction_date'
                ])
                ->orderBy('mod_gocardless_matches.created_at', 'desc')
                ->limit($numItems);

            $matches = $matchesQuery->get();

            // Get match count
            $pendingMatchesCount = Capsule::table('mod_gocardless_matches')
                ->where('status', 'pending')
                ->count();

            // Get daily stats
            $todayTotal = Capsule::table('mod_gocardless_transactions')
                ->whereDate('transaction_date', date('Y-m-d'))
                ->sum('amount');

            // Get matched vs unmatched stats
            $matchedCount = Capsule::table('mod_gocardless_transactions')
                ->where('status', 'matched')
                ->count();

            $unmatchedCount = Capsule::table('mod_gocardless_transactions')
                ->where('status', 'unmatched')
                ->count();

            // Enhance invoice data
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
                'transactions' => $transactions,
                'matches' => $matches,
                'pendingMatchesCount' => $pendingMatchesCount,
                'todayTotal' => $todayTotal,
                'matchedCount' => $matchedCount,
                'unmatchedCount' => $unmatchedCount,
                'moduleLink' => 'addonmodules.php?module=gocardless_openbanking'
            ];
        } catch (\Exception $e) {
            return [
                'error' => $e->getMessage()
            ];
        }
    }

    /**
     * Generate widget content
     *
     * @param array $data Widget data
     * @return string
     */
    public function generateOutput($data)
    {
        // Check for error
        if (isset($data['error'])) {
            return '
            <div class="widget-content-padded">
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i> ' . $data['error'] . '
                </div>
            </div>';
        }

        // Widget HTML
        $output = '
        <div class="widget-content-padded">
            <div class="row">
                <div class="col-sm-4 text-center">
                    <h3>' . number_format($data['todayTotal'], 2) . '</h3>
                    <p>Today\'s Transactions</p>
                </div>
                <div class="col-sm-4 text-center">
                    <h3>' . $data['pendingMatchesCount'] . '</h3>
                    <p>Pending Matches</p>
                </div>
                <div class="col-sm-4 text-center">
                    <h3>' . $data['matchedCount'] . ' / ' . $data['unmatchedCount'] . '</h3>
                    <p>Matched / Unmatched</p>
                </div>
            </div>
            
            <ul class="nav nav-tabs" role="tablist">
                <li role="presentation" class="active">
                    <a href="#gocardless-transactions" aria-controls="transactions" role="tab" data-toggle="tab">Recent Transactions</a>
                </li>
                <li role="presentation">
                    <a href="#gocardless-matches" aria-controls="matches" role="tab" data-toggle="tab">Pending Matches</a>
                </li>
            </ul>
            
            <div class="tab-content">
                <div role="tabpanel" class="tab-pane active" id="gocardless-transactions">
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <tr>
                                <th>Date</th>
                                <th>Amount</th>
                                <th>Bank</th>
                                <th>Status</th>
                            </tr>';

        // Add transaction rows
        if (count($data['transactions']) > 0) {
            foreach ($data['transactions'] as $transaction) {
                $statusClass = $transaction->status == 'matched' ? 'success' : 'warning';
                $date = date('Y-m-d', strtotime($transaction->transaction_date));
                $amount = number_format($transaction->amount, 2) . ' ' . $transaction->currency;
                
                $output .= '
                <tr>
                    <td>' . $date . '</td>
                    <td>' . $amount . '</td>
                    <td>' . $transaction->bank_name . '</td>
                    <td><span class="label label-' . $statusClass . '">' . $transaction->status . '</span></td>
                </tr>';
            }
        } else {
            $output .= '
                <tr>
                    <td colspan="4" class="text-center">No transactions found</td>
                </tr>';
        }

        $output .= '
                        </table>
                    </div>
                </div>
                <div role="tabpanel" class="tab-pane" id="gocardless-matches">
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <tr>
                                <th>Date</th>
                                <th>Amount</th>
                                <th>Invoice</th>
                                <th>Confidence</th>
                            </tr>';

        // Add matches rows
        if (count($data['matches']) > 0) {
            foreach ($data['matches'] as $match) {
                $date = date('Y-m-d', strtotime($match->transaction_date));
                $amount = number_format($match->amount, 2) . ' ' . $match->currency;
                
                $confidenceClass = 'warning';
                if ($match->confidence >= 0.9) {
                    $confidenceClass = 'success';
                } elseif ($match->confidence >= 0.7) {
                    $confidenceClass = 'info';
                }
                
                $confidencePercent = round($match->confidence * 100) . '%';
                
                $output .= '
                <tr>
                    <td>' . $date . '</td>
                    <td>' . $amount . '</td>
                    <td><a href="invoices.php?action=edit&id=' . $match->invoice_id . '">#' . $match->invoice_number . '</a></td>
                    <td><span class="label label-' . $confidenceClass . '">' . $confidencePercent . '</span></td>
                </tr>';
            }
        } else {
            $output .= '
                <tr>
                    <td colspan="4" class="text-center">No pending matches found</td>
                </tr>';
        }

        $output .= '
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="text-right">
                <a href="' . $data['moduleLink'] . '" class="btn btn-default btn-sm">
                    <i class="fas fa-external-link-alt"></i> Open GoCardless Dashboard
                </a>
            </div>
        </div>';

        return $output;
    }
}
