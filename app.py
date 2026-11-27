import os
import secrets
from flask import Flask, request, send_from_directory, abort
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
PASSWORD = os.environ.get("UPLOAD_PASSWORD", "")
ALLOWED = {"jpg", "jpeg", "png", "gif", "mp4", "mov", "webm"}

PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Upload</title>
<style>
body{font-family:sans-serif;max-width:480px;margin:40px auto;padding:0 16px}
input,button{width:100%;padding:12px;margin:8px 0;font-size:16px;box-sizing:border-box}
button{background:#2563eb;color:#fff;border:0;border-radius:8px}
code{word-break:break-all;background:#eee;padding:8px;display:block;border-radius:6px}
</style></head><body>
<h2>Upload photo / video</h2>
{msg}
<form method="post" action="/upload" enctype="multipart/form-data">
<input type="password" name="password" placeholder="Password" required>
<input type="file" name="file" accept="image/*,video/*" required>
<button type="submit">Upload</button>
</form></body></html>"""


@app.get("/")
def index():
    return PAGE.replace("{msg}", "")


@app.post("/upload")
def upload():
    if not PASSWORD or not secrets.compare_digest(request.form.get("password", ""), PASSWORD):
        return PAGE.replace("{msg}", "<p style='color:red'>Wrong password</p>"), 403
    f = request.files.get("file")
    if not f or "." not in f.filename:
        return PAGE.replace("{msg}", "<p style='color:red'>No file</p>"), 400
    ext = f.filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED:
        return PAGE.replace("{msg}", "<p style='color:red'>File type not allowed</p>"), 400
    name = secrets.token_urlsafe(12) + "." + ext
    f.save(os.path.join(UPLOAD_DIR, name))
    link = request.host_url.rstrip("/") + "/f/" + name
    return PAGE.replace("{msg}", "<p>Done. Copy this link:</p><code>" + link + "</code>")


@app.get("/f/<name>")
def serve(name):
    if "/" in name or ".." in name:
        abort(404)
    return send_from_directory(UPLOAD_DIR, name)
