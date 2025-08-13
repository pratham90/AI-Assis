from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
import sys
import platform

# Ensure imports work when running from backend directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from gpt_engine import GPTEngine
from resume_parser import extract_text_from_pdf

def get_frontend_build_dir() -> str:
    """Resolve the path to the React build directory, compatible with PyInstaller."""
    # If packaged by PyInstaller, data is under _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        packaged_dir = os.path.join(sys._MEIPASS, 'frontend', 'build')
        if os.path.exists(packaged_dir):
            return packaged_dir
    # Default: use workspace build dir
    return os.path.join(PROJECT_ROOT, 'frontend', 'build')

FRONTEND_BUILD_DIR = get_frontend_build_dir()
print(f"[DEBUG] Frontend build dir: {FRONTEND_BUILD_DIR}")
print(f"[DEBUG] Frontend build exists: {os.path.exists(FRONTEND_BUILD_DIR)}")

app = Flask(__name__, static_folder=FRONTEND_BUILD_DIR, static_url_path='')

# OS-safe absolute upload directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR

# Allow requests from frontend
CORS(app)

gpt_engine = GPTEngine()

@app.route('/listen', methods=['POST'])
def listen():
    # Basic implementation: echo back received data or status
    data = request.get_json(silent=True) or {}
    return jsonify({'status': 'listening', 'received': data})

@app.get('/health')
def health():
    return jsonify({
        'status': 'ok',
        'os': platform.system(),
        'release': platform.release(),
        'platform': platform.platform()
    })


@app.route('/ask', methods=['POST'])
def ask():
    # Log the OS type for each request (cross-platform support)
    print(f"[DEBUG] Backend running on OS: {platform.system()} {platform.release()} ({platform.platform()})")
    # If multipart/form-data, handle file upload
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        question = request.form.get('question', '')
        mode = request.form.get('mode', 'global')
        history = request.form.get('history', None)
        resume_file = request.files.get('resume')
        resume_text = None
        if resume_file:
            filename = secure_filename(resume_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            resume_file.save(file_path)
            # Always use the same logic as desktop: parse PDF or text
            if filename.lower().endswith('.pdf'):
                resume_text = extract_text_from_pdf(file_path)
            else:
                # Try to parse as text, fallback to empty string if error
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        resume_text = f.read()
                except Exception:
                    resume_text = ''
            # Debug print: show filename and first 200 chars of resume text
            print(f"[DEBUG] Resume file received: {filename}")
            print(f"[DEBUG] Resume text length: {len(resume_text) if resume_text else 0}")
            print("[DEBUG] Resume text preview (first 200 chars):\n", (resume_text or '')[:200])
            if not resume_text or not resume_text.strip():
                print(f"[WARNING] Resume text is empty after extraction for file: {filename}")
        else:
            resume_text = None
        # Parse history if present
        import json as _json
        if history:
            try:
                history = _json.loads(history)
            except Exception:
                history = []
        else:
            history = []
        if not question:
            return jsonify({'answer': 'No question provided.'}), 400
        
        # CRITICAL FIX: If Smart mode is requested, ALWAYS use resume mode regardless of resume_text
        if mode == 'resume':
            print(f"[DEBUG] Smart mode requested - using resume context (resume_text_len={len(resume_text) if resume_text else 0})")
            if not resume_text or not resume_text.strip():
                return jsonify({
                    'answer': 'Could not extract any text from the uploaded resume. If your PDF is a scanned image, try a text-based PDF or upload a .txt file instead.'
                }), 422
            answer = gpt_engine.generate_response(question, resume_text=resume_text, mode="resume", history=history)
        else:
            # Global mode
            answer = gpt_engine.generate_response(question, resume_text=resume_text, mode="global", history=history)
        
        return jsonify({'answer': answer})
    # Else, handle JSON (old flow)
    data = request.get_json()
    question = data.get('question', '')
    resume = data.get('resume', None)
    mode = data.get('mode', 'global')
    history = data.get('history', [])
    if not question:
        return jsonify({'answer': 'No question provided.'}), 400
    answer = gpt_engine.generate_response(question, resume_text=resume, mode=mode, history=history)
    return jsonify({'answer': answer})


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path: str):
    if path == '':
        return send_from_directory(FRONTEND_BUILD_DIR, 'index.html')
    return app.send_static_file(path)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    app.run(host=host, port=port, debug=False)
