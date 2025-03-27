from flask_backend.app import app
import os
import sys
import werkzeug.serving

if __name__ == "__main__":
    # Intercept the root URL before Flask even sees it
    # Set an environment variable that our app will check
    os.environ['DEFAULT_DASHBOARD'] = 'nobleui'
    
    # Log that we're trying to override
    print("Starting with NobleUI as the default dashboard...")
    
    # Run the app
    app.run(host="0.0.0.0", port=5000, debug=True)