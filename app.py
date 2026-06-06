import os
from app import create_app

# Create Flask app instance
app = create_app()

if __name__ == '__main__':
    # Retrieve port and host settings from environment variables
    port = int(os.environ.get('PORT', 5001))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting Smart Job Matching System on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
