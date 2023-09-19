from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image, ExifTags
import os
import imghdr
import uuid
import time

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Límite de tamaño de archivo: 16MB

def allowed_file(filename):
    allowed = '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    if not allowed:
        flash('Formato de archivo no permitido. Por favor, use .jpg, .jpeg, .png o .gif', 'error')
    return allowed

def generate_unique_filename(filename):
    unique_id = str(uuid.uuid4())
    return f"{unique_id}_{filename}"

def extract_metadata(image_path):
    metadata = {}
    with Image.open(image_path) as img:
        exif_data = img._getexif()
        if exif_data:
            for tag, value in exif_data.items():
                if tag in ExifTags.TAGS:
                    metadata[ExifTags.TAGS[tag]] = value
    return metadata

def remove_metadata(image_path):
    try:
        with Image.open(image_path) as img:
            img_without_metadata = Image.new(img.mode, img.size)
            img_without_metadata.putdata(list(img.getdata()))

            temp_filename = generate_unique_filename(os.path.basename(image_path))
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)

            img_without_metadata.save(temp_path)
        return temp_path
    except Exception as e:
        flash(f'Error al procesar la imagen: {e}', 'error')
        return None

def remove_old_images(folder_path, max_age_seconds):
    current_time = time.time()

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getctime(file_path)
            if file_age > max_age_seconds:
                os.remove(file_path)

# Llamar a esta función para eliminar imágenes antiguas
remove_old_images('static/images', 24 * 60 * 60)  # Elimina imágenes más antiguas de 24 horas

@app.route('/', methods=['GET', 'POST'])
def index():
    edited_image_path = None  # Define la variable antes de usarla
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No se ha seleccionado ningún archivo', 'error')
            return redirect(request.url)
        
        image = request.files['image']
        if image.filename == '':
            flash('No se ha seleccionado ningún archivo', 'error')
            return redirect(request.url)

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)  # Guarda la imagen
            metadata = extract_metadata(image_path)
            
            if not metadata:  # Si no hay metadatos
                flash('La imagen no contiene metadatos.', 'error')
            
            if 'GPSInfo' in metadata:
                edited_image_path = remove_metadata(image_path)
            
            return render_template('index.html.j2', image_path=image_path, metadata=metadata, edited_image_path=edited_image_path)
        else:
            flash('Tipo de archivo no permitido o inválido', 'error')

    return render_template('index.html.j2', edited_image_path=edited_image_path)

@app.route('/download/<filename>')
def download(filename):
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(image_path):
        _, file_extension = os.path.splitext(filename)
        mimetype = 'image/jpeg' if file_extension.lower() in ['.jpg', '.jpeg'] else 'image/png'
        return send_file(image_path, as_attachment=True, mimetype=mimetype, download_name=f"edited_{filename}")
    else:
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
