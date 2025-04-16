from flask_backend.app import app
import os
import sys
import werkzeug.serving

if __name__ == "__main__":
    # Set an environment variable that our app will check
    # Force the NobleUI dashboard to be the default
    os.environ['DEFAULT_DASHBOARD'] = 'nobleui'
    os.environ['FORCE_NOBLEUI'] = 'true'
    
    # Log that we're forcing NobleUI
    print("Starting with NobleUI dashboard FORCED...")
    print("Root URL will redirect directly to the NobleUI dashboard")
    
    # Run the app
    app.run(host="0.0.0.0", port=5000, debug=True)