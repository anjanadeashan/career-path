import os
import nltk

# Vercel's filesystem is read-only except /tmp — redirect NLTK data writes there
nltk.data.path.insert(0, '/tmp/nltk_data')
os.environ.setdefault('NLTK_DATA', '/tmp/nltk_data')

from app import create_app

# Create Flask app instance
app = create_app()

if __name__ == '__main__':
    # Retrieve port and host settings from environment variables
    port = int(os.environ.get('PORT', 5001))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting Smart Job Matching System on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
