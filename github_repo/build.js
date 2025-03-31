/**
 * Simple build script for Netlify deployment
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Log with timestamp
function log(message) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${message}`);
}

// Main build function
async function build() {
  log('Starting build process for Netlify deployment');
  
  // Check if flask_backend/static exists
  const staticDir = path.join(__dirname, 'flask_backend', 'static');
  if (!fs.existsSync(staticDir)) {
    log('Error: Static directory not found!');
    process.exit(1);
  }
  
  log(`Static directory found at ${staticDir}`);
  log('Checking for required static files...');
  
  // Check for index.html
  const indexPath = path.join(staticDir, 'index.html');
  if (!fs.existsSync(indexPath)) {
    log('Warning: index.html not found in static directory. Site may not work correctly.');
  } else {
    log('Found index.html');
  }
  
  // Check for NobleUI template directory
  const nobleUiTemplateDir = path.join(staticDir, 'nobleui');
  if (!fs.existsSync(nobleUiTemplateDir)) {
    log('Warning: NobleUI template directory not found in static directory. Creating a placeholder structure.');
    fs.mkdirSync(path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'demo1', 'pages', 'ui-components'), { recursive: true });
    fs.mkdirSync(path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'demo1', 'pages', 'forms'), { recursive: true });
    fs.mkdirSync(path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'demo1', 'pages', 'charts'), { recursive: true });
    fs.mkdirSync(path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'demo1', 'pages', 'tables'), { recursive: true });
    fs.mkdirSync(path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'demo1', 'pages', 'auth'), { recursive: true });
    fs.mkdirSync(path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'demo1', 'pages', 'general'), { recursive: true });
    fs.mkdirSync(path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'assets', 'css', 'demo1'), { recursive: true });
  } else {
    log('Found NobleUI template directory');
  }
  
  // Create placeholder HTML files if they don't exist
  const placeholderFiles = [
    path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'demo1', 'dashboard.html'),
    path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'demo1', 'pages', 'ui-components', 'accordion.html'),
    path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'demo1', 'pages', 'forms', 'basic-elements.html'),
    path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'demo1', 'pages', 'charts', 'apex.html'),
    path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'demo1', 'pages', 'tables', 'basic-table.html'),
    path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'demo1', 'pages', 'auth', 'login.html'),
    path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'demo1', 'pages', 'general', 'profile.html')
  ];
  
  const placeholderContent = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NobleUI Template</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
  <div class="container py-5 text-center">
    <h1>NobleUI Template Placeholder</h1>
    <p class="lead">This is a placeholder for the actual NobleUI template.</p>
    <p>To view the real NobleUI templates, please copy the full NobleUI theme files to this directory.</p>
    <div class="mt-4">
      <a href="/" class="btn btn-primary">Back to Home</a>
    </div>
  </div>
</body>
</html>
  `.trim();
  
  placeholderFiles.forEach(file => {
    if (!fs.existsSync(file)) {
      const dir = path.dirname(file);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.writeFileSync(file, placeholderContent);
      log(`Created placeholder file: ${file}`);
    }
  });
  
  // Create placeholder CSS file
  const placeholderCssFile = path.join(nobleUiTemplateDir, 'NobleUI-HTML-v3.0', 'template', 'assets', 'css', 'demo1', 'style.css');
  if (!fs.existsSync(placeholderCssFile)) {
    const dir = path.dirname(placeholderCssFile);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(placeholderCssFile, '/* Placeholder CSS file */');
    log(`Created placeholder CSS file: ${placeholderCssFile}`);
  }
  
  // Check for CSS files
  const cssDir = path.join(staticDir, 'css');
  if (!fs.existsSync(cssDir)) {
    log('Creating CSS directory');
    fs.mkdirSync(cssDir, { recursive: true });
  }
  
  // Check for JS files
  const jsDir = path.join(staticDir, 'js');
  if (!fs.existsSync(jsDir)) {
    log('Creating JS directory');
    fs.mkdirSync(jsDir, { recursive: true });
  }
  
  // Create netlify.toml in the static directory for proper configuration
  const netlifyConfig = `
# This file is used by Netlify to configure your site
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
`;
  
  fs.writeFileSync(path.join(staticDir, 'netlify.toml'), netlifyConfig);
  log('Created netlify.toml in static directory');
  
  // Create a _redirects file for Netlify (alternative to netlify.toml)
  fs.writeFileSync(path.join(staticDir, '_redirects'), '/* /index.html 200');
  log('Created _redirects file for Netlify');

  log('Build process completed successfully');
}

// Run the build
build().catch(error => {
  console.error('Build failed:', error);
  process.exit(1);
}); 