<div class="gocardless-configuration">
    <div class="alert alert-info">
        <i class="fas fa-info-circle"></i> Manage your GoCardless Open Banking connections and settings here.
    </div>
    
    {if isset($smarty.session.gocardless_message)}
        {$smarty.session.gocardless_message}
        {php}unset($_SESSION['gocardless_message']);{/php}
    {/if}
    
    <!-- Current Settings -->
    <div class="panel panel-default">
        <div class="panel-heading">
            <h3 class="panel-title">Current Settings</h3>
        </div>
        <div class="panel-body">
            <div class="row">
                <div class="col-md-6">
                    <div class="form-group">
                        <label>GoCardless API Key:</label>
                        <div class="input-group">
                            <input type="password" class="form-control" value="********" readonly>
                            <span class="input-group-btn">
                                <a href="configaddonmods.php?module=gocardless_openbanking" class="btn btn-default">
                                    <i class="fas fa-pencil-alt"></i> Edit
                                </a>
                            </span>
                        </div>
                        <small class="text-muted">API Key is stored securely</small>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="form-group">
                        <label>Cron Frequency:</label>
                        <div class="input-group">
                            <input type="text" class="form-control" value="{$moduleParams.cron_frequency}" readonly>
                            <span class="input-group-btn">
                                <a href="configaddonmods.php?module=gocardless_openbanking" class="btn btn-default">
                                    <i class="fas fa-pencil-alt"></i> Edit
                                </a>
                            </span>
                        </div>
                        <small class="text-muted">How often transactions are retrieved</small>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="form-group">
                        <label>Automatic Matching:</label>
                        <div class="input-group">
                            <input type="text" class="form-control" value="{if $moduleParams.auto_matching == 'on'}Enabled{else}Disabled{/if}" readonly>
                            <span class="input-group-btn">
                                <a href="configaddonmods.php?module=gocardless_openbanking" class="btn btn-default">
                                    <i class="fas fa-pencil-alt"></i> Edit
                                </a>
                            </span>
                        </div>
                        <small class="text-muted">Automatically match transactions to invoices</small>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="form-group">
                        <label>Auto-Apply Matches:</label>
                        <div class="input-group">
                            <input type="text" class="form-control" value="{if $moduleParams.auto_apply == 'on'}Enabled{else}Disabled{/if}" readonly>
                            <span class="input-group-btn">
                                <a href="configaddonmods.php?module=gocardless_openbanking" class="btn btn-default">
                                    <i class="fas fa-pencil-alt"></i> Edit
                                </a>
                            </span>
                        </div>
                        <small class="text-muted">Automatically apply confirmed matches</small>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="form-group">
                        <label>Matching Confidence Threshold:</label>
                        <div class="input-group">
                            <input type="text" class="form-control" value="{$moduleParams.matching_confidence}" readonly>
                            <span class="input-group-btn">
                                <a href="configaddonmods.php?module=gocardless_openbanking" class="btn btn-default">
                                    <i class="fas fa-pencil-alt"></i> Edit
                                </a>
                            </span>
                        </div>
                        <small class="text-muted">Confidence level required for matches</small>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="form-group">
                        <label>Debug Mode:</label>
                        <div class="input-group">
                            <input type="text" class="form-control" value="{if $moduleParams.debug_mode == 'on'}Enabled{else}Disabled{/if}" readonly>
                            <span class="input-group-btn">
                                <a href="configaddonmods.php?module=gocardless_openbanking" class="btn btn-default">
                                    <i class="fas fa-pencil-alt"></i> Edit
                                </a>
                            </span>
                        </div>
                        <small class="text-muted">Enable for detailed logging</small>
                    </div>
                </div>
            </div>
        </div>
        <div class="panel-footer">
            <div class="row">
                <div class="col-md-6">
                    <form method="post" action="{$moduleLink}">
                        <input type="hidden" name="form_action" value="run_cron">
                        <button type="submit" class="btn btn-default">
                            <i class="fas fa-sync"></i> Run Cron Job Now
                        </button>
                    </form>
                </div>
                <div class="col-md-6 text-right">
                    <a href="configaddonmods.php?module=gocardless_openbanking" class="btn btn-primary">
                        <i class="fas fa-cog"></i> Modify All Settings
                    </a>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Connected Bank Accounts -->
    <div class="panel panel-default">
        <div class="panel-heading">
            <h3 class="panel-title">Connected Bank Accounts</h3>
        </div>
        <div class="panel-body">
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Bank</th>
                            <th>Account Name</th>
                            <th>Account ID</th>
                            <th>Currency</th>
                            <th>Status</th>
                            <th>Connected On</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {if count($accounts) > 0}
                            {foreach from=$accounts item=account}
                                <tr>
                                    <td>{$account->bank_name}</td>
                                    <td>{$account->account_name}</td>
                                    <td>{$account->account_id}</td>
                                    <td>{$account->currency}</td>
                                    <td>
                                        {if $account->status == 'active'}
                                            <span class="label label-success">Active</span>
                                        {elseif $account->status == 'token_expired'}
                                            <span class="label label-warning">Token Expired</span>
                                        {else}
                                            <span class="label label-default">{$account->status}</span>
                                        {/if}
                                    </td>
                                    <td>{$account->created_at|date_format:"%Y-%m-%d"}</td>
                                    <td>
                                        <form method="post" action="{$moduleLink}" onsubmit="return confirm('Are you sure you want to remove this bank connection?');">
                                            <input type="hidden" name="form_action" value="remove_bank">
                                            <input type="hidden" name="account_id" value="{$account->account_id}">
                                            <button type="submit" class="btn btn-xs btn-danger">
                                                <i class="fas fa-trash"></i> Remove
                                            </button>
                                        </form>
                                    </td>
                                </tr>
                            {/foreach}
                        {else}
                            <tr>
                                <td colspan="7" class="text-center">No bank accounts connected yet</td>
                            </tr>
                        {/if}
                    </tbody>
                </table>
            </div>
        </div>
        <div class="panel-footer">
            <form method="post" action="{$moduleLink}">
                <input type="hidden" name="form_action" value="add_bank">
                <button type="submit" class="btn btn-success">
                    <i class="fas fa-plus-circle"></i> Connect New Bank Account
                </button>
            </form>
        </div>
    </div>
    
    <!-- Instructions -->
    <div class="panel panel-info">
        <div class="panel-heading">
            <h3 class="panel-title">How to Set Up</h3>
        </div>
        <div class="panel-body">
            <ol>
                <li>
                    <strong>Configure API Credentials</strong>
                    <p>Enter your GoCardless API credentials in the module configuration.</p>
                </li>
                <li>
                    <strong>Connect Bank Accounts</strong>
                    <p>Click "Connect New Bank Account" and follow the OAuth flow to authorize access.</p>
                </li>
                <li>
                    <strong>Configure Cron Job</strong>
                    <p>Ensure WHMCS cron job is running regularly to fetch transactions automatically.</p>
                </li>
                <li>
                    <strong>Review Matching Settings</strong>
                    <p>Configure automatic matching and confidence thresholds to suit your needs.</p>
                </li>
            </ol>
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i> 
                <strong>Note:</strong> Bank connections may require periodic reauthorization. If a connection shows "Token Expired", you'll need to reconnect that bank.
            </div>
        </div>
    </div>
</div>
