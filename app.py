from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import zipfile
import io

app = Flask(__name__)

# Konfigurasi Database (SQLite lokal)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prabu.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Konfigurasi Folder Upload
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Inisialisasi Database
db = SQLAlchemy(app)

# Struktur Tabel Database
class Pendaftar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    kelas = db.Column(db.String(20), nullable=False)
    alasan = db.Column(db.Text, nullable=False)
    cv = db.Column(db.String(255))
    transkrip = db.Column(db.String(255))
    swot = db.Column(db.String(255))
    ijazah = db.Column(db.String(255))

with app.app_context():
    db.create_all()

@app.route('/')
def form_rekrutmen():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        nama = request.form['namaLengkap']
        kelas = request.form['kelas']
        alasan = request.form['alasan']
        
        cv = request.files['cv']
        transkrip = request.files['transkrip']
        swot = request.files['swot']
        ijazah = request.files['ijazah']

        cv_name = secure_filename(cv.filename)
        transkrip_name = secure_filename(transkrip.filename)
        swot_name = secure_filename(swot.filename)
        ijazah_name = secure_filename(ijazah.filename)

        cv.save(os.path.join(app.config['UPLOAD_FOLDER'], cv_name))
        transkrip.save(os.path.join(app.config['UPLOAD_FOLDER'], transkrip_name))
        swot.save(os.path.join(app.config['UPLOAD_FOLDER'], swot_name))
        ijazah.save(os.path.join(app.config['UPLOAD_FOLDER'], ijazah_name))

        pendaftar_baru = Pendaftar(
            nama=nama, 
            kelas=kelas, 
            alasan=alasan, 
            cv=cv_name, 
            transkrip=transkrip_name, 
            swot=swot_name, 
            ijazah=ijazah_name
        )
        db.session.add(pendaftar_baru)
        db.session.commit()

        return render_template('sukses.html', nama=nama)

@app.route('/dashboard')
def dashboard():
    # Mengambil data dan mengurutkannya berdasarkan kelas secara berurutan (X-1, X-2, dst)
    data_pendaftar = Pendaftar.query.order_by(Pendaftar.kelas.asc()).all()
    return render_template('dashboard.html', pendaftar=data_pendaftar)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ROUTE BARU: Untuk mendownload semua berkas 1 orang dalam bentuk file .ZIP
@app.route('/download-zip/<int:id_pendaftar>')
def download_zip(id_pendaftar):
    pendaftar = Pendaftar.query.get_or_404(id_pendaftar)
    
    # Buat file ZIP di dalam memori komputer (tidak menumpuk file sampah di server)
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        files_to_zip = [
            (pendaftar.cv, "CV_"),
            (pendaftar.transkrip, "Transkrip_"),
            (pendaftar.swot, "SWOT_"),
            (pendaftar.ijazah, "Ijazah_")
        ]
        
        for filename, prefix in files_to_zip:
            if filename:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    # Menambahkan nama pendaftar di depan nama file dalam zip agar tidak tertukar
                    arcname = f"{prefix}_{pendaftar.nama}_{filename}"
                    zf.write(file_path, arcname)
                    
    memory_file.seek(0)
    
    # Nama file ZIP hasil download nanti (Contoh: Berkas_Aimar_X-5.zip)
    zip_filename = f"Berkas_{pendaftar.nama.replace(' ', '_')}_{pendaftar.kelas}.zip"
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )

if __name__ == '__main__':
    app.run(debug=True)