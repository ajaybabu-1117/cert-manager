from flask import Flask, render_template, request, redirect, send_file, flash, session, url_for
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import io

# Load .env variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key")

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
db = client.get_default_database()
fs = GridFS(db)

# Config
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Helper
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 🔐 Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '1117':
            session['logged_in'] = True
            flash('Login successful!', 'success')
            return redirect('/')
        else:
            flash('Incorrect password.', 'danger')
    return render_template('login.html')

# 🔓 Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out successfully.', 'info')
    return redirect('/login')

# Home
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect('/login')
    try:
        files = fs.find()
        return render_template("index.html", files=files)
    except Exception as e:
        flash(f"Error loading files: {e}", "danger")
        return redirect('/login')

# Upload
@app.route('/upload', methods=['POST'])
def upload():
    if not session.get('logged_in'):
        return redirect('/login')
    
    title = request.form.get('title', '').strip()
    file = request.files.get('file')

    if not title or not file:
        flash('Title and file are required.', 'danger')
        return redirect('/')

    if not allowed_file(file.filename):
        flash('Only PDF, JPG, and PNG files allowed.', 'danger')
        return redirect('/')

    filename = secure_filename(title)
    try:
        fs.put(file, filename=filename)
        flash('Certificate uploaded successfully!', 'success')
    except Exception as e:
        flash(f'Upload failed: {e}', 'danger')
    return redirect('/')

# Download
@app.route('/download/<file_id>')
def download(file_id):
    if not session.get('logged_in'):
        return redirect('/login')
    
    try:
        file = fs.get(ObjectId(file_id))
        return send_file(io.BytesIO(file.read()), download_name=file.filename, as_attachment=True)
    except Exception as e:
        flash(f'File not found: {e}', 'danger')
        return redirect('/')

# Delete
@app.route('/delete/<file_id>')
def delete(file_id):
    if not session.get('logged_in'):
        return redirect('/login')
    
    try:
        fs.delete(ObjectId(file_id))
        flash('Certificate deleted.', 'success')
    except Exception as e:
        flash(f'Delete failed: {e}', 'danger')
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
