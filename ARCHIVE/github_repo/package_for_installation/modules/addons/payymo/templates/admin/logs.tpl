<div class="gocardless-logs">
    <div class="alert alert-info">
        <i class="fas fa-info-circle"></i> View logs for the GoCardless Open Banking integration.
    </div>
    
    {if isset($smarty.session.gocardless_message)}
        {$smarty.session.gocardless_message}
        {php}unset($_SESSION['gocardless_message']);{/php}
    {/if}
    
    <!-- Filter Form -->
    <div class="panel panel-default">
        <div class="panel-heading">
            <h3 class="panel-title">Filter Logs</h3>
        </div>
        <div class="panel-body">
            <form method="get" action="{$moduleLink}">
                <input type="hidden" name="module" value="gocardless_openbanking">
                <input type="hidden" name="action" value="logs">
                <div class="row">
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="level">Log Level</label>
                            <select name="level" id="level" class="form-control">
                                <option value="">All Levels</option>
                                <option value="debug" {if $level == 'debug'}selected{/if}>Debug</option>
                                <option value="info" {if $level == 'info'}selected{/if}>Info</option>
                                <option value="warning" {if $level == 'warning'}selected{/if}>Warning</option>
                                <option value="error" {if $level == 'error'}selected{/if}>Error</option>
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
                            <input type="text" name="search" id="search" class="form-control" placeholder="Search log messages..." value="{$search}">
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12 text-right">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-search"></i> Filter
                        </button>
                        <a href="{$moduleLink}&action=logs" class="btn btn-default">
                            <i class="fas fa-times"></i> Clear
                        </a>
                    </div>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Logs Table -->
    <div class="panel panel-default">
        <div class="panel-heading">
            <div class="row">
                <div class="col-md-6">
                    <h3 class="panel-title">System Logs</h3>
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
                            <th>Date/Time</th>
                            <th>Level</th>
                            <th>Message</th>
                            <th>Context</th>
                        </tr>
                    </thead>
                    <tbody>
                        {if count($logs) > 0}
                            {foreach from=$logs item=log}
                                <tr>
                                    <td>{$log->created_at}</td>
                                    <td>
                                        {if $log->level == 'error'}
                                            <span class="label label-danger">Error</span>
                                        {elseif $log->level == 'warning'}
                                            <span class="label label-warning">Warning</span>
                                        {elseif $log->level == 'info'}
                                            <span class="label label-info">Info</span>
                                        {elseif $log->level == 'debug'}
                                            <span class="label label-default">Debug</span>
                                        {else}
                                            <span class="label label-default">{$log->level}</span>
                                        {/if}
                                    </td>
                                    <td>{$log->message}</td>
                                    <td>
                                        {if $log->context}
                                            <button type="button" class="btn btn-xs btn-default" onclick="showContext('{$log->id}')">
                                                <i class="fas fa-eye"></i> View
                                            </button>
                                            <div id="context-{$log->id}" class="hidden">
                                                <pre>{$log->context}</pre>
                                            </div>
                                        {else}
                                            -
                                        {/if}
                                    </td>
                                </tr>
                            {/foreach}
                        {else}
                            <tr>
                                <td colspan="4" class="text-center">No logs found</td>
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
                            <a href="{$moduleLink}&action=logs&page=1{if $level}&level={$level}{/if}{if $dateFrom}&date_from={$dateFrom}{/if}{if $dateTo}&date_to={$dateTo}{/if}{if $search}&search={$search}{/if}" aria-label="First">
                                <span aria-hidden="true">&laquo;&laquo;</span>
                            </a>
                        </li>
                        <li>
                            <a href="{$moduleLink}&action=logs&page={$page-1}{if $level}&level={$level}{/if}{if $dateFrom}&date_from={$dateFrom}{/if}{if $dateTo}&date_to={$dateTo}{/if}{if $search}&search={$search}{/if}" aria-label="Previous">
                                <span aria-hidden="true">&laquo;</span>
                            </a>
                        </li>
                    {/if}
                    
                    {for $p=max(1, $page-2) to min($totalPages, $page+2)}
                        <li{if $p == $page} class="active"{/if}>
                            <a href="{$moduleLink}&action=logs&page={$p}{if $level}&level={$level}{/if}{if $dateFrom}&date_from={$dateFrom}{/if}{if $dateTo}&date_to={$dateTo}{/if}{if $search}&search={$search}{/if}">
                                {$p}
                            </a>
                        </li>
                    {/for}
                    
                    {if $page < $totalPages}
                        <li>
                            <a href="{$moduleLink}&action=logs&page={$page+1}{if $level}&level={$level}{/if}{if $dateFrom}&date_from={$dateFrom}{/if}{if $dateTo}&date_to={$dateTo}{/if}{if $search}&search={$search}{/if}" aria-label="Next">
                                <span aria-hidden="true">&raquo;</span>
                            </a>
                        </li>
                        <li>
                            <a href="{$moduleLink}&action=logs&page={$totalPages}{if $level}&level={$level}{/if}{if $dateFrom}&date_from={$dateFrom}{/if}{if $dateTo}&date_to={$dateTo}{/if}{if $search}&search={$search}{/if}" aria-label="Last">
                                <span aria-hidden="true">&raquo;&raquo;</span>
                            </a>
                        </li>
                    {/if}
                </ul>
            </div>
            
            <!-- Clear Logs Form -->
            <hr>
            <form method="post" action="{$moduleLink}" onsubmit="return confirm('Are you sure you want to clear old logs?');" class="text-right">
                <input type="hidden" name="form_action" value="clear_logs">
                <div class="form-inline">
                    <div class="form-group">
                        <label for="days">Clear logs older than</label>
                        <select name="days" id="days" class="form-control">
                            <option value="7">7 days</option>
                            <option value="14">14 days</option>
                            <option value="30" selected>30 days</option>
                            <option value="60">60 days</option>
                            <option value="90">90 days</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-danger">
                        <i class="fas fa-trash"></i> Clear Old Logs
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Context Modal -->
<div class="modal fade" id="contextModal" tabindex="-1" role="dialog" aria-labelledby="contextModalLabel">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                <h4 class="modal-title" id="contextModalLabel">Log Context</h4>
            </div>
            <div class="modal-body">
                <pre id="contextModalContent"></pre>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>

<script type="text/javascript">
function showContext(logId) {
    var context = $('#context-' + logId).html();
    $('#contextModalContent').html(context);
    $('#contextModal').modal('show');
}
</script>
