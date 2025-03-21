<div class="gocardless-license">
    <div class="alert alert-info">
        <i class="fas fa-info-circle"></i> Manage your GoCardless Open Banking module license.
    </div>
    
    {if isset($smarty.session.gocardless_message)}
        {$smarty.session.gocardless_message}
        {php}unset($_SESSION['gocardless_message']);{/php}
    {/if}
    
    {if isset($error)}
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-circle"></i> {$error}
        </div>
    {/if}
    
    <!-- License Status Card -->
    <div class="row">
        <div class="col-md-8 col-md-offset-2">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <h3 class="panel-title">License Status</h3>
                </div>
                <div class="panel-body text-center">
                    {if $license_status == 'valid'}
                        <i class="fas fa-check-circle fa-5x text-success"></i>
                        <h3 class="text-success">License Valid</h3>
                        <p>Your license key is valid and active.</p>
                    {else}
                        <i class="fas fa-times-circle fa-5x text-danger"></i>
                        <h3 class="text-danger">License Invalid</h3>
                        <p>Your license key is invalid or has expired.</p>
                    {/if}
                    
                    <hr>
                    
                    <div class="row">
                        <div class="col-md-8 col-md-offset-2">
                            <table class="table">
                                <tr>
                                    <th>License Key:</th>
                                    <td>
                                        <code>{$license_key|truncate:16:"***":true}</code>
                                        <a href="configaddonmods.php?module=gocardless_openbanking" class="btn btn-xs btn-default">
                                            <i class="fas fa-pencil-alt"></i> Change
                                        </a>
                                    </td>
                                </tr>
                                {if $license_status == 'valid' && isset($license_info)}
                                    <tr>
                                        <th>Registered To:</th>
                                        <td>{$license_info.registered_to}</td>
                                    </tr>
                                    <tr>
                                        <th>Expires:</th>
                                        <td>{$license_info.expires}</td>
                                    </tr>
                                    <tr>
                                        <th>Features:</th>
                                        <td>
                                            {if isset($license_info.features) && is_array($license_info.features)}
                                                <ul class="list-unstyled">
                                                    {foreach from=$license_info.features key=feature item=enabled}
                                                        <li>
                                                            {if $enabled}
                                                                <i class="fas fa-check text-success"></i>
                                                            {else}
                                                                <i class="fas fa-times text-danger"></i>
                                                            {/if}
                                                            {$feature|replace:'_':' '|capitalize}
                                                        </li>
                                                    {/foreach}
                                                </ul>
                                            {else}
                                                <p class="text-muted">No feature information available</p>
                                            {/if}
                                        </td>
                                    </tr>
                                {/if}
                            </table>
                        </div>
                    </div>
                </div>
                <div class="panel-footer text-center">
                    <a href="configaddonmods.php?module=gocardless_openbanking" class="btn btn-primary">
                        <i class="fas fa-cog"></i> Update License Key
                    </a>
                    <a href="{$moduleLink}&action=license&verify=1" class="btn btn-default">
                        <i class="fas fa-sync"></i> Verify License
                    </a>
                </div>
            </div>
        </div>
    </div>
    
    <!-- License Information -->
    <div class="panel panel-info">
        <div class="panel-heading">
            <h3 class="panel-title">About Licensing</h3>
        </div>
        <div class="panel-body">
            <div class="row">
                <div class="col-md-6">
                    <h4>License Features</h4>
                    <ul>
                        <li>Connect to multiple banks via GoCardless Open Banking API</li>
                        <li>Automatic transaction retrieval via scheduled cron jobs</li>
                        <li>Intelligent invoice matching algorithms</li>
                        <li>Admin dashboard with detailed transaction reports</li>
                        <li>Technical support and updates</li>
                    </ul>
                </div>
                <div class="col-md-6">
                    <h4>License FAQ</h4>
                    <dl>
                        <dt>How do I purchase a license?</dt>
                        <dd>Visit our website to purchase a new license or renew an existing one.</dd>
                        
                        <dt>Where do I enter my license key?</dt>
                        <dd>Go to Setup → Addon Modules → GoCardless Open Banking → Configure</dd>
                        
                        <dt>How often is my license verified?</dt>
                        <dd>Your license is verified daily and when an administrator logs in.</dd>
                        
                        <dt>What happens if my license expires?</dt>
                        <dd>The module will continue to work but will no longer receive updates or support.</dd>
                    </dl>
                </div>
            </div>
            <hr>
            <div class="text-center">
                <p>Need help with your license? Contact our support team.</p>
                <a href="https://example.com/support" target="_blank" class="btn btn-info">
                    <i class="fas fa-life-ring"></i> Contact Support
                </a>
                <a href="https://example.com/licenses" target="_blank" class="btn btn-success">
                    <i class="fas fa-shopping-cart"></i> Purchase/Renew License
                </a>
            </div>
        </div>
    </div>
</div>
