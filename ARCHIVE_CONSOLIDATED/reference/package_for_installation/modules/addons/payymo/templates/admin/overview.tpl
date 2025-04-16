<div class="gocardless-overview">
    <div class="alert alert-info">
        <i class="fas fa-info-circle"></i> Welcome to the GoCardless Open Banking integration. This module helps you automatically retrieve bank transactions and match them to invoices.
    </div>
    
    {if isset($smarty.session.gocardless_message)}
        {$smarty.session.gocardless_message}
        {php}unset($_SESSION['gocardless_message']);{/php}
    {/if}
    
    <!-- Statistics Cards -->
    <div class="row">
        <div class="col-md-3">
            <div class="panel panel-default">
                <div class="panel-body text-center">
                    <h2>{$matchPercentage}%</h2>
                    <p>Match Rate</p>
                </div>
                <div class="panel-footer text-center">
                    <span class="text-success">{$matchedCount}</span> Matched / 
                    <span class="text-warning">{$unmatchedCount}</span> Unmatched
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="panel panel-default">
                <div class="panel-body text-center">
                    <h2>{count($pendingMatches)}</h2>
                    <p>Pending Matches</p>
                </div>
                <div class="panel-footer text-center">
                    <a href="{$moduleLink}&action=matches" class="btn btn-xs btn-default">View All</a>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="panel panel-default">
                <div class="panel-body text-center">
                    <h2>{count($transactions)}</h2>
                    <p>Recent Transactions</p>
                </div>
                <div class="panel-footer text-center">
                    <a href="{$moduleLink}&action=transactions" class="btn btn-xs btn-default">View All</a>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="panel panel-default">
                <div class="panel-body text-center">
                    <h2>{$banksCount}</h2>
                    <p>Connected Banks</p>
                </div>
                <div class="panel-footer text-center">
                    <a href="{$moduleLink}&action=configuration" class="btn btn-xs btn-default">Manage</a>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Actions Panel -->
    <div class="panel panel-default">
        <div class="panel-heading">
            <h3 class="panel-title">Quick Actions</h3>
        </div>
        <div class="panel-body">
            <div class="row">
                <div class="col-md-4">
                    <form method="post" action="{$moduleLink}">
                        <input type="hidden" name="form_action" value="run_cron">
                        <button type="submit" class="btn btn-default btn-block">
                            <i class="fas fa-sync"></i> Refresh Transactions
                        </button>
                    </form>
                </div>
                <div class="col-md-4">
                    <a href="{$moduleLink}&action=matches" class="btn btn-primary btn-block">
                        <i class="fas fa-exchange-alt"></i> Process Matches ({count($pendingMatches)})
                    </a>
                </div>
                <div class="col-md-4">
                    <a href="{$moduleLink}&action=configuration" class="btn btn-success btn-block">
                        <i class="fas fa-plus-circle"></i> Add Bank Connection
                    </a>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Transactions Chart -->
    <div class="panel panel-default">
        <div class="panel-heading">
            <h3 class="panel-title">Transaction Activity (Last 7 Days)</h3>
        </div>
        <div class="panel-body">
            <canvas id="transactionsChart" height="100"></canvas>
        </div>
    </div>
    
    <!-- Recent Transactions -->
    <div class="panel panel-default">
        <div class="panel-heading">
            <h3 class="panel-title">Recent Transactions</h3>
        </div>
        <div class="panel-body">
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Transaction ID</th>
                            <th>Amount</th>
                            <th>Bank</th>
                            <th>Description</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {if count($transactions) > 0}
                            {foreach from=$transactions item=transaction}
                                <tr>
                                    <td>{$transaction->transaction_date|date_format:"%Y-%m-%d"}</td>
                                    <td>{$transaction->transaction_id}</td>
                                    <td>{$transaction->amount} {$transaction->currency}</td>
                                    <td>{$transaction->bank_name}</td>
                                    <td title="{$transaction->description}">{$transaction->description|truncate:30:"..."}</td>
                                    <td>
                                        {if $transaction->status == 'matched'}
                                            <span class="label label-success">Matched</span>
                                        {else}
                                            <span class="label label-warning">Unmatched</span>
                                        {/if}
                                    </td>
                                    <td>
                                        <a href="{$moduleLink}&action=transactions&search={$transaction->transaction_id}" class="btn btn-xs btn-default">
                                            <i class="fas fa-search"></i> Details
                                        </a>
                                    </td>
                                </tr>
                            {/foreach}
                        {else}
                            <tr>
                                <td colspan="7" class="text-center">No transactions found</td>
                            </tr>
                        {/if}
                    </tbody>
                </table>
            </div>
        </div>
        <div class="panel-footer">
            <a href="{$moduleLink}&action=transactions" class="btn btn-default btn-sm">View All Transactions</a>
        </div>
    </div>
    
    <!-- Pending Matches -->
    <div class="panel panel-default">
        <div class="panel-heading">
            <h3 class="panel-title">Pending Matches</h3>
        </div>
        <div class="panel-body">
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Transaction</th>
                            <th>Amount</th>
                            <th>Invoice</th>
                            <th>Confidence</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {if count($pendingMatches) > 0}
                            {foreach from=$pendingMatches item=match}
                                <tr>
                                    <td>{$match->created_at|date_format:"%Y-%m-%d"}</td>
                                    <td title="Transaction ID: {$match->transaction_ref}">{$match->transaction_ref|truncate:15:"..."}</td>
                                    <td>{$match->amount} {$match->currency}</td>
                                    <td>
                                        <a href="invoices.php?action=edit&id={$match->invoice_id}" target="_blank">
                                            Invoice #{$match->invoice_id}
                                        </a>
                                    </td>
                                    <td>
                                        {if $match->confidence >= 0.9}
                                            <span class="label label-success">{($match->confidence * 100)|string_format:"%d"}%</span>
                                        {elseif $match->confidence >= 0.7}
                                            <span class="label label-info">{($match->confidence * 100)|string_format:"%d"}%</span>
                                        {else}
                                            <span class="label label-warning">{($match->confidence * 100)|string_format:"%d"}%</span>
                                        {/if}
                                    </td>
                                    <td>
                                        <div class="btn-group">
                                            <form method="post" action="{$moduleLink}" style="display:inline;">
                                                <input type="hidden" name="form_action" value="approve_match">
                                                <input type="hidden" name="match_id" value="{$match->id}">
                                                <button type="submit" class="btn btn-xs btn-success">
                                                    <i class="fas fa-check"></i> Approve
                                                </button>
                                            </form>
                                            &nbsp;
                                            <form method="post" action="{$moduleLink}" style="display:inline;">
                                                <input type="hidden" name="form_action" value="reject_match">
                                                <input type="hidden" name="match_id" value="{$match->id}">
                                                <button type="submit" class="btn btn-xs btn-danger">
                                                    <i class="fas fa-times"></i> Reject
                                                </button>
                                            </form>
                                        </div>
                                    </td>
                                </tr>
                            {/foreach}
                        {else}
                            <tr>
                                <td colspan="6" class="text-center">No pending matches found</td>
                            </tr>
                        {/if}
                    </tbody>
                </table>
            </div>
        </div>
        <div class="panel-footer">
            <a href="{$moduleLink}&action=matches" class="btn btn-default btn-sm">View All Matches</a>
        </div>
    </div>
</div>

<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/chart.js@3.7.0/dist/chart.min.js"></script>
<script type="text/javascript">
document.addEventListener('DOMContentLoaded', function() {
    // Transaction chart data
    var chartDates = {$chartDates};
    var chartAmounts = {$chartAmounts};
    var chartCounts = {$chartCounts};
    
    var ctx = document.getElementById('transactionsChart').getContext('2d');
    var chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartDates,
            datasets: [
                {
                    label: 'Amount',
                    yAxisID: 'y',
                    data: chartAmounts,
                    backgroundColor: 'rgba(79, 70, 229, 0.6)',
                    borderColor: 'rgba(79, 70, 229, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Count',
                    yAxisID: 'y1',
                    data: chartCounts,
                    type: 'line',
                    fill: false,
                    backgroundColor: 'rgba(147, 51, 234, 0.6)',
                    borderColor: 'rgba(147, 51, 234, 1)',
                    borderWidth: 2,
                    pointRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Amount'
                    }
                },
                y1: {
                    beginAtZero: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false
                    },
                    title: {
                        display: true,
                        text: 'Count'
                    }
                }
            }
        }
    });
});
</script>
