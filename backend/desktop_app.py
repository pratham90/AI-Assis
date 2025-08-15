

# Minimal PyWebView app: only runs Flask backend and launches the UI
import threading
import time
import webview
import os
import sys
from api_server import app

def expose_quit_api():
    def quit():
        try:
            webview.windows[0].destroy()
        except Exception:
            pass
        os._exit(0)
    if hasattr(webview, 'expose'):
        webview.expose(quit)
        return quit
    else:
        class Api:
            def quit(self):
                quit()
        return Api()

def run_flask():
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port, debug=False, use_reloader=False)

def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(1.5)
    url = 'http://127.0.0.1:5000/'
    window = webview.create_window(
        'System Monitor',
        url,
        width=900,
        height=600,
        resizable=True,
        on_top=True,
        frameless=True,
        transparent=True,
        easy_drag=True,
        min_size=(400, 300),
        text_select=False,
        confirm_close=False,
        x=100,
        y=100
    )
    api = expose_quit_api()
    webview.start(api, debug=False)

if __name__ == '__main__':
    main()