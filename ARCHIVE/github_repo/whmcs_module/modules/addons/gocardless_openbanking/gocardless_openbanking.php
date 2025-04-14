<?php
/**
 * GoCardless Open Banking Integration Module for WHMCS
 *
 * @copyright Copyright (c) 2023
 * @license https://opensource.org/licenses/MIT MIT License
 */

if (!defined("WHMCS")) {
    die("This file cannot be accessed directly");
}

use WHMCS\Database\Capsule;

/**
 * Define addon module configuration
 *
 * @return array
 */
function gocardless_openbanking_config() {
    return [
        'name' => 'GoCardless Open Banking',
        'description' => 'Integration with GoCardless Open Banking API for automated transaction retrieval and invoice reconciliation.',
        'author' => 'Your Company Name',
        'language' => 'english',
        'version' => '1.0',
        'fields' => [
            'api_key' => [
                'FriendlyName' => 'GoCardless API Key',
                'Type' => 'password',
                'Size' => '60',
                'Default' => '',
                'Description' => 'Enter your GoCardless API Key',
            ],
            'api_secret' => [
                'FriendlyName' => 'GoCardless API Secret',
                'Type' => 'password',
                'Size' => '60',
                'Default' => '',
                'Description' => 'Enter your GoCardless API Secret',
            ],
            'license_key' => [
                'FriendlyName' => 'License Key',
                'Type' => 'text',
                'Size' => '60',
                'Default' => '',
                'Description' => 'Enter your license key for this module',
            ],
            'cron_frequency' => [
                'FriendlyName' => 'Cron Frequency',
                'Type' => 'dropdown',
                'Options' => [
                    'hourly' => 'Hourly',
                    'every4hours' => 'Every 4 Hours',
                    'every12hours' => 'Every 12 Hours',
                    'daily' => 'Daily',
                ],
                'Default' => 'daily',
                'Description' => 'How often to run the transaction retrieval cron job',
            ],
            'auto_matching' => [
                'FriendlyName' => 'Automatic Matching',
                'Type' => 'yesno',
                'Default' => 'yes',
                'Description' => 'Enable automatic matching of transactions to invoices',
            ],
            'auto_apply' => [
                'FriendlyName' => 'Auto Apply Matches',
                'Type' => 'yesno',
                'Default' => 'no',
                'Description' => 'Automatically apply confirmed matches without admin approval',
            ],
            'matching_confidence' => [
                'FriendlyName' => 'Matching Confidence Threshold',
                'Type' => 'dropdown',
                'Options' => [
                    'low' => 'Low (60% match)',
                    'medium' => 'Medium (75% match)',
                    'high' => 'High (90% match)',
                    'exact' => 'Exact match only',
                ],
                'Default' => 'medium',
                'Description' => 'Confidence level required for automatic matching',
            ],
            'api_endpoint' => [
                'FriendlyName' => 'Flask API Endpoint',
                'Type' => 'text',
                'Size' => '60',
                'Default' => 'http://localhost:5000',
                'Description' => 'URL of the Flask backend API',
            ],
            'debug_mode' => [
                'FriendlyName' => 'Debug Mode',
                'Type' => 'yesno',
                'Default' => 'no',
                'Description' => 'Enable detailed logging for debugging',
            ],
        ],
    ];
}

/**
 * Addon module activation function
 *
 * @return array
 */
function gocardless_openbanking_activate() {
    try {
        // Create transactions table
        if (!Capsule::schema()->hasTable('mod_gocardless_transactions')) {
            Capsule::schema()->create('mod_gocardless_transactions', function ($table) {
                $table->increments('id');
                $table->string('transaction_id', 100)->unique();
                $table->string('bank_name', 100);
                $table->string('account_id', 100);
                $table->string('account_name', 100)->nullable();
                $table->decimal('amount', 10, 2);
                $table->string('currency', 3);
                $table->string('description', 255)->nullable();
                $table->string('reference', 100)->nullable();
                $table->dateTime('transaction_date');
                $table->integer('invoice_id')->nullable();
                $table->string('status', 20)->default('unmatched');
                $table->timestamps();
                $table->index('transaction_id');
                $table->index('invoice_id');
                $table->index('status');
            });
        }

        // Create bank accounts table
        if (!Capsule::schema()->hasTable('mod_gocardless_accounts')) {
            Capsule::schema()->create('mod_gocardless_accounts', function ($table) {
                $table->increments('id');
                $table->string('account_id', 100)->unique();
                $table->string('bank_id', 100);
                $table->string('bank_name', 100);
                $table->string('account_name', 100);
                $table->string('currency', 3);
                $table->string('oauth_token', 255);
                $table->dateTime('token_expires')->nullable();
                $table->string('status', 20)->default('active');
                $table->timestamps();
            });
        }

        // Create matching suggestions table
        if (!Capsule::schema()->hasTable('mod_gocardless_matches')) {
            Capsule::schema()->create('mod_gocardless_matches', function ($table) {
                $table->increments('id');
                $table->integer('transaction_id');
                $table->integer('invoice_id');
                $table->decimal('confidence', 5, 2);
                $table->string('match_reason', 255);
                $table->string('status', 20)->default('pending');
                $table->timestamps();
                $table->unique(['transaction_id', 'invoice_id']);
            });
        }

        // Create logs table
        if (!Capsule::schema()->hasTable('mod_gocardless_logs')) {
            Capsule::schema()->create('mod_gocardless_logs', function ($table) {
                $table->increments('id');
                $table->string('level', 20);
                $table->text('message');
                $table->text('context')->nullable();
                $table->timestamp('created_at')->useCurrent();
            });
        }

        return [
            'status' => 'success',
            'description' => 'GoCardless Open Banking module activated successfully.',
        ];
    } catch (\Exception $e) {
        return [
            'status' => 'error',
            'description' => 'Could not activate module: ' . $e->getMessage(),
        ];
    }
}

/**
 * Addon module deactivation function
 *
 * @return array
 */
function gocardless_openbanking_deactivate() {
    try {
        // We don't drop tables on deactivation to preserve data
        // Tables will be removed only if user chooses to uninstall

        return [
            'status' => 'success',
            'description' => 'GoCardless Open Banking module deactivated successfully. Database tables have been preserved.',
        ];
    } catch (\Exception $e) {
        return [
            'status' => 'error',
            'description' => 'Could not deactivate module: ' . $e->getMessage(),
        ];
    }
}

/**
 * Addon module upgrade function
 *
 * @param array $vars Module configuration parameters
 * @return array
 */
function gocardless_openbanking_upgrade($vars) {
    $version = $vars['version'];

    // Handle version-specific upgrades here
    switch ($version) {
        case '1.0':
            // Placeholder for future upgrades
            break;
    }

    return [
        'status' => 'success',
        'description' => 'GoCardless Open Banking module upgraded successfully.',
    ];
}

/**
 * Admin area output
 *
 * @param array $vars Module configuration parameters
 * @return string HTML output
 */
function gocardless_openbanking_output($vars) {
    require_once __DIR__ . '/lib/Admin.php';
    
    $admin = new GoCardlessOpenBanking\Admin();
    return $admin->dispatch($vars);
}

/**
 * Admin area sidebar output
 *
 * @param array $vars Module configuration parameters
 * @return array Sidebar items
 */
function gocardless_openbanking_sidebar($vars) {
    $moduleLink = $vars['modulelink'];
    
    return [
        'Dashboard' => [
            'icon' => 'fas fa-home',
            'link' => $moduleLink,
            'order' => 1,
        ],
        'Transactions' => [
            'icon' => 'fas fa-exchange-alt',
            'link' => $moduleLink . '&action=transactions',
            'order' => 2,
        ],
        'Matches' => [
            'icon' => 'fas fa-link',
            'link' => $moduleLink . '&action=matches',
            'order' => 3,
        ],
        'Configuration' => [
            'icon' => 'fas fa-cogs',
            'link' => $moduleLink . '&action=configuration',
            'order' => 4,
        ],
        'Logs' => [
            'icon' => 'fas fa-list',
            'link' => $moduleLink . '&action=logs',
            'order' => 5,
        ],
        'License' => [
            'icon' => 'fas fa-key',
            'link' => $moduleLink . '&action=license',
            'order' => 6,
        ],
    ];
}

/**
 * Client area output
 *
 * @param array $vars Module configuration parameters
 * @return array Client area output template and variables
 */
function gocardless_openbanking_clientarea($vars) {
    // This module doesn't have client area functionality
    return [
        'pagetitle' => 'GoCardless Open Banking',
        'breadcrumb' => [
            'index.php?m=gocardless_openbanking' => 'GoCardless Open Banking',
        ],
        'templatefile' => 'clientarea',
        'requirelogin' => true,
        'vars' => [
            'modulelink' => $vars['modulelink'],
            'LANG' => $vars['_lang'],
        ],
    ];
}
