from flask_backend.app import app
from flask import redirect, url_for

# Override the root route at the very last moment
@app.route('/', endpoint='root_index_override')
def root_index_override():
    """Root route that directly calls the NobleUI dashboard view function"""
    from flask_backend.routes_fresh import nobleui_dashboard
    return nobleui_dashboard()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)