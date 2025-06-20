from flask import Flask, render_template, request, redirect, send_file, flash, url_for
from flask_pymongo import PyMongo
from gridfs import GridFS
from bson import ObjectId
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import io

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key")

mongo = PyMongo(app)
fs = GridFS(mongo.db)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    files = fs.find()
    return render_template("index.html", files=files)

@app.route('/upload', methods=['POST'])
def upload():
    title = request.form.get('title', '').strip()
    file = request.files.get('file')

    if not title or not file:
        flash('Title and file are required.', 'danger')
        return redirect('/')

    if not allowed_file(file.filename):
        flash('Only PDF, JPG, and PNG files allowed.', 'danger')
        return redirect('/')

    filename = secure_filename(title)
    fs.put(file, filename=filename)
    flash('Certificate uploaded successfully!', 'success')
    return redirect('/')

@app.route('/download/<file_id>')
def download(file_id):
    try:
        file = fs.get(ObjectId(file_id))
        return send_file(io.BytesIO(file.read()), download_name=file.filename, as_attachment=True)
    except:
        flash('File not found.', 'danger')
        return redirect('/')

@app.route('/delete/<file_id>')
def delete(file_id):
    try:
        fs.delete(ObjectId(file_id))
        flash('Certificate deleted.', 'success')
    except:
        flash('Delete failed.', 'danger')
    return redirect('/')
