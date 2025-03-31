/**
 * Screenshot capture script for NobleUI dashboard
 * 
 * Prerequisites:
 * - Node.js installed
 * - npm install puppeteer
 * 
 * Usage:
 * - node capture_screenshot.js
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// Ensure the screenshots directory exists
const screenshotsDir = path.join(__dirname);
if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
}

// URLs to capture
const urls = [
    {
        url: 'http://localhost:5000/nobleui-dashboard',
        outputPath: path.join(screenshotsDir, 'nobleui_dashboard_light.png'),
        theme: 'light'
    },
    {
        url: 'http://localhost:5000/nobleui-dashboard',
        outputPath: path.join(screenshotsDir, 'nobleui_dashboard_dark.png'),
        theme: 'dark'
    }
];

// Capture screenshots
async function captureScreenshots() {
    // Launch browser
    const browser = await puppeteer.launch({
        headless: 'new',
        defaultViewport: {
            width: 1920,
            height: 1080
        },
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
        for (const config of urls) {
            // Create a new page
            const page = await browser.newPage();
            
            // Navigate to URL
            await page.goto(config.url, { waitUntil: 'networkidle2' });
            
            // Set theme if needed
            if (config.theme) {
                await page.evaluate((theme) => {
                    document.documentElement.setAttribute('data-bs-theme', theme);
                    
                    // If there's a theme switcher on the page, update its state
                    const themeSwitch = document.getElementById('themeSwitch');
                    if (themeSwitch) {
                        themeSwitch.checked = theme === 'dark';
                    }
                }, config.theme);
                
                // Wait a bit for any theme transitions
                await page.waitForTimeout(1000);
            }
            
            // Take screenshot
            await page.screenshot({
                path: config.outputPath,
                fullPage: true
            });
            
            console.log(`Screenshot saved to ${config.outputPath}`);
            
            // Close the page
            await page.close();
        }
    } catch (error) {
        console.error('Error capturing screenshots:', error);
    } finally {
        // Close browser
        await browser.close();
    }
}

// Run the script
captureScreenshots().catch(console.error); 