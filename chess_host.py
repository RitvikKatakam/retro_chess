import os
import sys
import subprocess
import time
from threading import Lock
from flask import Flask, render_template_string, redirect, url_for, send_from_directory

APP = Flask(__name__)
GAME_FILENAME = "main.py"
GAME_PATH = os.path.abspath(GAME_FILENAME)

# Add static folder configuration
APP.config['STATIC_FOLDER'] = 'static'
os.makedirs(APP.config['STATIC_FOLDER'], exist_ok=True)

proc_lock = Lock()
game_proc = None
proc_started_at = None

INDEX_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Retro Chess</title>
<style>
    body {
        background: url('/static/bg.png') no-repeat center center fixed;
        background-size: cover;
        font-family: system-ui, Arial, sans-serif;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100vh;
        margin: 0;
    }
    .box {
        background: rgba(0,0,0,0.75);
        padding: 40px 60px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }
    h1 {
        font-size: 48px;
        margin-bottom: 30px;
        color: #ffd700;
        text-shadow: 2px 2px 6px black;
    }
    button {
        padding: 20px 60px;
        font-size: 24px;
        border: none;
        border-radius: 8px;
        background-color: #4caf50;
        color: white;
        cursor: pointer;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        transition: background 0.3s;
    }
    button:hover {
        background-color: #45a049;
    }
</style>
</head>
<body>
    <div class="box">
        <h1>Retro Chess</h1>
        <form method="post" action="/start">
            <button type="submit">Play</button>
        </form>
    </div>
</body>
</html>
"""

# Add route to serve static files
@APP.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(APP.config['STATIC_FOLDER'], filename)

def game_file_exists():
    return os.path.isfile(GAME_PATH)

@APP.route("/")
def index():
    return render_template_string(INDEX_HTML)

@APP.route("/start", methods=["POST"])
def start():
    global game_proc, proc_started_at
    if not game_file_exists():
        return "Game file not found on server: {}".format(GAME_PATH), 404
    with proc_lock:
        if game_proc is not None and game_proc.poll() is None:
            return "Game already running."
        try:
            cmd = [sys.executable, GAME_PATH]
            game_proc = subprocess.Popen(cmd)
            proc_started_at = time.time()
        except Exception as e:
            game_proc = None
            proc_started_at = None
            return "Failed to start: {}".format(e), 500
    return redirect(url_for("index"))

if __name__ == "__main__":
    print(f"Serving Retro Chess from: {GAME_PATH}")
    print(f"Static files folder: {APP.config['STATIC_FOLDER']}")
    print("Please make sure bg.png is in the static folder")
    APP.run(debug=True, host="127.0.0.1", port=5000)