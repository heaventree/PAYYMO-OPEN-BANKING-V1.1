<div class="gocardless-transactions">
    <div class="alert alert-info">
        <i class="fas fa-info-circle"></i> View and manage bank transactions retrieved from GoCardless Open Banking.
    </div>
    
    {if isset($smarty.session.gocardless_message)}
        {$smarty.session.gocardless_message}
        {php}unset($_SESSION['gocardless_message']);{/php}
    {/if}
    
    <!-- Filter Form -->
    <div class="panel panel-default">
        <div class="panel-heading">
            <h3 class="panel-title">Filter Transactions</h3>
        </div>
        <div class="panel-body">
            <form method="get" action="{$moduleLink}">
                <input type="hidden" name="module" value="gocardless_openbanking">
                <input type="hidden" name="action" value="transactions">
                <div class="row">
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="status">Status</label>
                            <select name="status" id="status" class="form-control">
                                <option value="">All Statuses</option>
                                <option value="matched" {if $status == 'matched'}selected{/if}>Matched</option>
                                <option value="unmatched" {if $status == 'unmatched'}selected{/if}>Unmatched</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="date_from">From Date</label>
                            <input type="date" name="date_from" id="date_from" class="form-control" value="{$dateFrom}">
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="date_to">To Date</label>
                            <input type="date" name="date_to" id="date_to" class="form-control" value="{$dateTo}">
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="search">Search</label>
                            <input type="text" name="search" id="search" class="form-control" placeholder="Transaction ID, Bank, Description..." value="{$search}">
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12 text-right">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-search"></i> Filter
                        </button>
                        <a href="{$moduleLink}&action=transactions" class="btn btn-default">
                            <i class="fas fa-times"></i> Clear
                        </a>
                    </div>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Transactions Table -->
    <div class="panel panel-default">
        <div class="panel-heading">
            <div class="row">
                <div class="col-md-6">
                    <h3 class="panel-title">Transactions</h3>
                </div>
                <div class="col-md-6 text-right">
                    <span class="badge">{$totalRecords} total</span>
                </div>
            </div>
        </div>
        <div class="panel-body">
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Transaction ID</th>
                            <th>Bank Name</th>
                            <th>Account Name</th>
                            <th>Amount</th>
                            <th>Description</th>
                            <th>Reference</th>
                            <th>Status</th>
                            <th>Invoice</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {if count($transactions) > 0}
                            {foreach from=$transactions item=transaction}
                                <tr>
                                    <td>{$transaction->transaction_date|date_format:"%Y-%m-%d"}</td>
                                    <td title="{$transaction->transaction_id}">{$transaction->transaction_id|truncate:15:"..."}</td>
                                    <td>{$transaction->bank_name}</td>
                                    <td>{$transaction->account_name}</td>
                                    <td>{$transaction->amount} {$transaction->currency}</td>
                                    <td title="{$transaction->description}">{$transaction->description|truncate:25:"..."}</td>
                                    <td title="{$transaction->reference}">{$transaction->reference|truncate:15:"..."}</td>
                                    <td>
                                        {if $transaction->status == 'matched'}
                                            <span class="label label-success">Matched</span>
                                        {else}
                                            <span class="label label-warning">Unmatched</span>
                                        {/if}
                                    </td>
                                    <td>
                                        {if $transaction->invoice_id}
                                            <a href="invoices.php?action=edit&id={$transaction->invoice_id}" target="_blank">
                                                #{$transaction->invoice_id}
                                            </a>
                                        {else}
                                            -
                                        {/if}
                                    </td>
                                    <td>
                                        <div class="btn-group">
                                            <button type="button" class="btn btn-xs btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                                                <i class="fas fa-cog"></i> <span class="caret"></span>
                                            </button>
                                            <ul class="dropdown-menu dropdown-menu-right">
                                                <li>
                                                    <a href="#" onclick="showTransactionDetails({$transaction->id}); return false;">
                                                        <i class="fas fa-search"></i> View Details
                                                    </a>
                                                </li>
                                                {if $transaction->status != 'matched'}
                                                    <li>
                                                        <a href="{$moduleLink}&action=matches&transaction_id={$transaction->id}">
                                                            <i class="fas fa-link"></i> Find Matches
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a href="#" onclick="showManualMatchModal({$transaction->id}); return false;">
                                                            <i class="fas fa-hand-point-right"></i> Manual Match
                                                        </a>
                                                    </li>
                                                {/if}
                                            </ul>
                                        </div>
                                    </td>
                                </tr>
                            {/foreach}
                        {else}
                            <tr>
                                <td colspan="10" class="text-center">No transactions found</td>
                            </tr>
                        {/if}
                    </tbody>
                </table>
            </div>
        </div>
        <div class="panel-footer">
            <!-- Pagination -->
            <div class="text-center">
                <ul class="pagination">
                    {if $page > 1}
                        <li>
                            <a href="{$moduleLink}&action=transactions&page=1{if $status}&status={$status}{/if}{if $dateFrom}&date_from={$dateFrom}{/if}{if $dateTo}&date_to={$dateTo}{/if}{if $search}&search={$search}{/if}" aria-label="First">
                                <span aria-hidden="true">&laquo;&laquo;</span>
                            </a>
                        </li>
                        <li>
                            <a href="{$moduleLink}&action=transactions&page={$page-1}{if $status}&status={$status}{/if}{if $dateFrom}&date_from={$dateFrom}{/if}{if $dateTo}&date_to={$dateTo}{/if}{if $search}&search={$search}{/if}" aria-label="Previous">
                                <span aria-hidden="true">&laquo;</span>
                            </a>
                        </li>
                    {/if}
                    
                    {for $p=max(1, $page-2) to min($totalPages, $page+2)}
                        <li{if $p == $page} class="active"{/if}>
                            <a href="{$moduleLink}&action=transactions&page={$p}{if $status}&status={$status}{/if}{if $dateFrom}&date_from={$dateFrom}{/if}{if $dateTo}&date_to={$dateTo}{/if}{if $search}&search={$search}{/if}">
                                {$p}
                            </a>
                        </li>
                    {/for}
                    
                    {if $page < $totalPages}
                        <li>
                            <a href="{$moduleLink}&action=transactions&page={$page+1}{if $status}&status={$status}{/if}{if $dateFrom}&date_from={$dateFrom}{/if}{if $dateTo}&date_to={$dateTo}{/if}{if $search}&search={$search}{/if}" aria-label="Next">
                                <span aria-hidden="true">&raquo;</span>
                            </a>
                        </li>
                        <li>
                            <a href="{$moduleLink}&action=transactions&page={$totalPages}{if $status}&status={$status}{/if}{if $dateFrom}&date_from={$dateFrom}{/if}{if $dateTo}&date_to={$dateTo}{/if}{if $search}&search={$search}{/if}" aria-label="Last">
                                <span aria-hidden="true">&raquo;&raquo;</span>
                            </a>
                        </li>
                    {/if}
                </ul>
            </div>
        </div>
    </div>
</div>

<!-- Transaction Details Modal -->
<div class="modal fade" id="transactionDetailsModal" tabindex="-1" role="dialog" aria-labelledby="transactionDetailsLabel">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                <h4 class="modal-title" id="transactionDetailsLabel">Transaction Details</h4>
            </div>
            <div class="modal-body">
                <div id="transactionDetailsContent">
                    <div class="text-center">
                        <i class="fas fa-spinner fa-spin fa-3x"></i>
                        <p>Loading transaction details...</p>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>

<!-- Manual Match Modal -->
<div class="modal fade" id="manualMatchModal" tabindex="-1" role="dialog" aria-labelledby="manualMatchLabel">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                <h4 class="modal-title" id="manualMatchLabel">Manually Match Transaction</h4>
            </div>
            <div class="modal-body">
                <form id="manualMatchForm" action="{$moduleLink}" method="post">
                    <input type="hidden" name="form_action" value="manual_match">
                    <input type="hidden" name="transaction_id" id="manual_match_transaction_id" value="">
                    
                    <div class="form-group">
                        <label for="invoice_id">Invoice ID</label>
                        <input type="number" class="form-control" id="invoice_id" name="invoice_id" required placeholder="Enter the invoice ID to match">
                    </div>
                    
                    <div class="form-group">
                        <label>Confirm Match</label>
                        <div class="checkbox">
                            <label>
                                <input type="checkbox" name="confirm_match" required> 
                                I confirm this match is correct and payment should be applied
                            </label>
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onclick="submitManualMatch()">Apply Match</button>
            </div>
        </div>
    </div>
</div>

<script type="text/javascript">
function showTransactionDetails(transactionId) {
    // Clear previous content
    $('#transactionDetailsContent').html('<div class="text-center"><i class="fas fa-spinner fa-spin fa-3x"></i><p>Loading transaction details...</p></div>');
    
    // Show modal
    $('#transactionDetailsModal').modal('show');
    
    // Fetch transaction details via AJAX
    $.ajax({
        url: '{$moduleLink}&action=ajax_transaction_details',
        type: 'GET',
        data: {
            transaction_id: transactionId
        },
        success: function(response) {
            $('#transactionDetailsContent').html(response);
        },
        error: function(xhr, status, error) {
            $('#transactionDetailsContent').html('<div class="alert alert-danger">Error loading transaction details: ' + error + '</div>');
        }
    });
}

function showManualMatchModal(transactionId) {
    // Set transaction ID in the form
    $('#manual_match_transaction_id').val(transactionId);
    
    // Clear previous values
    $('#invoice_id').val('');
    $('#manualMatchForm input[type="checkbox"]').prop('checked', false);
    
    // Show modal
    $('#manualMatchModal').modal('show');
}

function submitManualMatch() {
    // Validate form
    if ($('#invoice_id').val() === '') {
        alert('Please enter an invoice ID');
        return;
    }
    
    if (!$('#manualMatchForm input[type="checkbox"]').is(':checked')) {
        alert('Please confirm the match');
        return;
    }
    
    // Submit form
    $('#manualMatchForm').submit();
}
</script>
