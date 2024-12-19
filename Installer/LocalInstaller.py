from flask import Flask, request, redirect, url_for, send_from_directory, render_template, flash
import os
from werkzeug.utils import secure_filename
from datetime import datetime

# Configuration
UPLOAD_FOLDER = 'uploads'  # Directory to save uploaded files
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'zip', 'rar', 'docx', 'xlsx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
HOST = '0.0.0.0'  # Accessible to other devices on the network
PORT = 5000

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Get file information
def get_file_info(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    # Get file size and last modified time
    size = os.path.getsize(filepath)
    mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))

    # Convert size to human-readable format
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            break
        size /= 1024.0

    return {
        'name': filename,
        'size': f'{size:.2f} {unit}',
        'modified': mod_time.strftime('%Y-%m-%d %H:%M:%S')
    }


# Route: Home (upload and list files)
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if files were uploaded
        if 'files[]' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)

        files = request.files.getlist('files[]')
        uploaded_files = []
        error_files = []

        for file in files:
            # Skip empty file submissions
            if file.filename == '':
                continue

            # Check if file is allowed
            if file and allowed_file(file.filename):
                try:
                    # Secure the filename to prevent directory traversal attacks
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    # Handle filename conflicts
                    counter = 1
                    while os.path.exists(filepath):
                        name, ext = os.path.splitext(filename)
                        filename = f"{name}_{counter}{ext}"
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        counter += 1

                    # Save the file
                    file.save(filepath)
                    uploaded_files.append(filename)
                except Exception as e:
                    error_files.append(file.filename)
            else:
                error_files.append(file.filename)

        # Flash messages for upload status
        if uploaded_files:
            flash(f'Successfully uploaded {len(uploaded_files)} file(s): {", ".join(uploaded_files)}', 'success')
        if error_files:
            flash(f'Failed to upload {len(error_files)} file(s): {", ".join(error_files)}', 'danger')

        return redirect(url_for('upload_file'))

    # Get file information for listing
    files = os.listdir(UPLOAD_FOLDER)
    file_info = [get_file_info(f) for f in files]

    return render_template('upload.html', files=file_info)


# Route: Download a file
@app.route('/uploads/<filename>')
def download_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        flash('File not found', 'danger')
        return redirect(url_for('upload_file'))


# Route: Delete a file
@app.route('/delete/<filename>')
def delete_file(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.remove(filepath)
        flash(f'File {filename} deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'danger')
    return redirect(url_for('upload_file'))


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)