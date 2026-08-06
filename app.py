import os
from flask import Flask, jsonify, render_template
from werkzeug.exceptions import RequestEntityTooLarge

from routes.embed_routes import embed_bp
from routes.extract_routes import extract_bp
from routes.detect_routes import detect_bp

app = Flask(__name__)

# Enforce 25 MB payload limit & disable static caching during dev
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def add_header(response):
    # Prevent browser caching stale assets
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

try:
    UPLOAD_FOLDER = '/tmp/uploads' if os.name != 'nt' else 'uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except Exception:
    pass

@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(e):
    return jsonify({
        "error": "The selected file is too large. Maximum upload size is 25 MB."
    }), 413

@app.route('/')
def index():
    return render_template("index.html")

# Feature routes
app.register_blueprint(embed_bp)
app.register_blueprint(extract_bp)
app.register_blueprint(detect_bp)

if __name__ == '__main__':
    app.run()