<div class="gocardless-matches">
    <div class="alert alert-info">
        <i class="fas fa-info-circle"></i> Review and process suggested matches between transactions and invoices.
    </div>
    
    {if isset($smarty.session.gocardless_message)}
        {$smarty.session.gocardless_message}
        {php}unset($_SESSION['gocardless_message']);{/php}
    {/if}
    
    <!-- Filter Form -->
    <div class="panel panel-default">
        <div class="panel-heading">
            <h3 class="panel-title">Filter Matches</h3>
        </div>
        <div class="panel-body">
            <form method="get" action="{$moduleLink}">
                <input type="hidden" name="module" value="gocardless_openbanking">
                <input type="hidden" name="action" value="matches">
                <div class="row">
                    <div class="col-md-4">
                        <div class="form-group">
                            <label for="status">Status</label>
                            <select name="status" id="status" class="form-control">
                                <option value="pending" {if $status == 'pending'}selected{/if}>Pending</option>
                                <option value="approved" {if $status == 'approved'}selected{/if}>Approved</option>
                                <option value="rejected" {if $status == 'rejected'}selected{/if}>Rejected</option>
                                <option value="" {if $status == ''}selected{/if}>All</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-8 text-right" style="padding-top: 25px;">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-search"></i> Filter
                        </button>
                        <a href="{$moduleLink}&action=matches" class="btn btn-default">
                            <i class="fas fa-times"></i> Clear
                        </a>
                    </div>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Matches Table -->
    <div class="panel panel-default">
        <div class="panel-heading">
            <div class="row">
                <div class="col-md-6">
                    <h3 class="panel-title">Suggested Matches</h3>
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
                            <th>Transaction Date</th>
                            <th>Transaction Details</th>
                            <th>Amount</th>
                            <th>Invoice</th>
                            <th>Client</th>
                            <th>Match Confidence</th>
                            <th>Match Reason</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {if count($matches) > 0}
                            {foreach from=$matches item=match}
                                <tr>
                                    <td>{$match->transaction_date|date_format:"%Y-%m-%d"}</td>
                                    <td>
                                        <strong title="{$match->transaction_ref}">{$match->transaction_ref|truncate:15:"..."}</strong><br>
                                        <small>{$match->bank_name}</small>
                                    </td>
                                    <td><strong>{$match->amount} {$match->currency}</strong></td>
                                    <td>
                                        <a href="invoices.php?action=edit&id={$match->invoice_id}" target="_blank">
                                            #{$match->invoice_number}
                                        </a><br>
                                        <small>{if isset($match->invoice_total)}{$match->invoice_total}{/if}</small>
                                    </td>
                                    <td>
                                        {if isset($match->client_id) && $match->client_id != 'N/A'}
                                            <a href="clientssummary.php?userid={$match->client_id}" target="_blank">
                                                {$match->client_name}
                                            </a>
                                        {else}
                                            {$match->client_name}
                                        {/if}
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
                                    <td>{$match->match_reason}</td>
                                    <td>
                                        {if $match->status == 'pending'}
                                            <span class="label label-warning">Pending</span>
                                        {elseif $match->status == 'approved'}
                                            <span class="label label-success">Approved</span>
                                        {elseif $match->status == 'rejected'}
                                            <span class="label label-danger">Rejected</span>
                                        {/if}
                                    </td>
                                    <td>
                                        {if $match->status == 'pending'}
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
                                        {else}
                                            <small class="text-muted">No actions available</small>
                                        {/if}
                                    </td>
                                </tr>
                            {/foreach}
                        {else}
                            <tr>
                                <td colspan="9" class="text-center">No matches found</td>
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
                            <a href="{$moduleLink}&action=matches&page=1{if $status}&status={$status}{/if}" aria-label="First">
                                <span aria-hidden="true">&laquo;&laquo;</span>
                            </a>
                        </li>
                        <li>
                            <a href="{$moduleLink}&action=matches&page={$page-1}{if $status}&status={$status}{/if}" aria-label="Previous">
                                <span aria-hidden="true">&laquo;</span>
                            </a>
                        </li>
                    {/if}
                    
                    {for $p=max(1, $page-2) to min($totalPages, $page+2)}
                        <li{if $p == $page} class="active"{/if}>
                            <a href="{$moduleLink}&action=matches&page={$p}{if $status}&status={$status}{/if}">
                                {$p}
                            </a>
                        </li>
                    {/for}
                    
                    {if $page < $totalPages}
                        <li>
                            <a href="{$moduleLink}&action=matches&page={$page+1}{if $status}&status={$status}{/if}" aria-label="Next">
                                <span aria-hidden="true">&raquo;</span>
                            </a>
                        </li>
                        <li>
                            <a href="{$moduleLink}&action=matches&page={$totalPages}{if $status}&status={$status}{/if}" aria-label="Last">
                                <span aria-hidden="true">&raquo;&raquo;</span>
                            </a>
                        </li>
                    {/if}
                </ul>
            </div>
            
            <!-- Bulk Actions -->
            {if $status == 'pending' && count($matches) > 0}
                <hr>
                <div class="row">
                    <div class="col-md-6">
                        <form id="bulkApproveForm" method="post" action="{$moduleLink}" onsubmit="return confirm('Are you sure you want to approve all visible matches?');">
                            <input type="hidden" name="form_action" value="bulk_approve">
                            <input type="hidden" name="status" value="{$status}">
                            <input type="hidden" name="page" value="{$page}">
                            <button type="submit" class="btn btn-success">
                                <i class="fas fa-check"></i> Approve All Visible
                            </button>
                        </form>
                    </div>
                    <div class="col-md-6 text-right">
                        <form id="bulkRejectForm" method="post" action="{$moduleLink}" onsubmit="return confirm('Are you sure you want to reject all visible matches?');">
                            <input type="hidden" name="form_action" value="bulk_reject">
                            <input type="hidden" name="status" value="{$status}">
                            <input type="hidden" name="page" value="{$page}">
                            <button type="submit" class="btn btn-danger">
                                <i class="fas fa-times"></i> Reject All Visible
                            </button>
                        </form>
                    </div>
                </div>
            {/if}
        </div>
    </div>
    
    <!-- Instructions Panel -->
    <div class="panel panel-info">
        <div class="panel-heading">
            <h3 class="panel-title">About Transaction Matching</h3>
        </div>
        <div class="panel-body">
            <p>The matching system uses multiple factors to suggest potential matches between bank transactions and WHMCS invoices:</p>
            <ul>
                <li><strong>Amount Matching:</strong> Exact or partial matches between transaction and invoice amounts.</li>
                <li><strong>Reference Numbers:</strong> Looks for invoice numbers in transaction references.</li>
                <li><strong>Client Information:</strong> Matches client names or details from transaction descriptions.</li>
                <li><strong>Date Proximity:</strong> Considers how close in time the transaction and invoice are.</li>
            </ul>
            <p>The <strong>Match Confidence</strong> percentage indicates how likely the match is to be correct.</p>
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i> 
                <strong>Important:</strong> Always review matches before approving, especially those with lower confidence scores.
            </div>
        </div>
    </div>
</div>
