from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, timezone
import os
import zipfile
import io
import csv

app = Flask(__name__)

# Konfigurasi Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prabu.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Konfigurasi Folder Upload
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Inisialisasi Database
db = SQLAlchemy(app)

# ==========================================
# PENGATURAN PENUTUPAN OTOMATIS
# ==========================================
# Zona waktu WIB (UTC+7) agar akurat meski di-hosting di server luar negeri
WIB = timezone(timedelta(hours=7))

# TENTUKAN KAPAN PENDAFTARAN DITUTUP (Tahun, Bulan, Tanggal, Jam, Menit, Detik)
# Contoh di bawah ini: 29 September 2026, jam 23:59:59
BATAS_WAKTU = datetime(2026, 9, 29, 23, 59, 59, tzinfo=WIB)

def cek_status():
    waktu_sekarang = datetime.now(WIB)
    if waktu_sekarang > BATAS_WAKTU:
        return 'TUTUP'
    return 'BUKA'
# ==========================================

# Struktur Tabel
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
    # Sistem otomatis mengecek apakah waktu saat ini sudah lewat batas
    return render_template('index.html', status=cek_status())

@app.route('/submit', methods=['POST'])
def submit():
    # Menolak data yang masuk jika sudah lewat batas jam 23:59
    if cek_status() == 'TUTUP':
        return "Mohon maaf, waktu pendaftaran Prabu Jakarta 2026 sudah resmi berakhir pada pukul 23:59!"
        
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
    data_pendaftar = Pendaftar.query.order_by(Pendaftar.kelas.asc()).all()
    return render_template('dashboard.html', pendaftar=data_pendaftar)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/download-zip/<int:id_pendaftar>')
def download_zip(id_pendaftar):
    pendaftar = Pendaftar.query.get_or_404(id_pendaftar)
    
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
                    arcname = f"{prefix}_{pendaftar.nama}_{filename}"
                    zf.write(file_path, arcname)
                    
    memory_file.seek(0)
    zip_filename = f"Berkas_{pendaftar.nama.replace(' ', '_')}_{pendaftar.kelas}.zip"
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )

@app.route('/export-csv')
def export_csv():
    data = Pendaftar.query.order_by(Pendaftar.kelas.asc()).all()
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Nama Lengkap', 'Kelas', 'Alasan Masuk'])
    
    for row in data:
        cw.writerow([row.id, row.nama, row.kelas, row.alasan])
        
    output = Response(si.getvalue(), mimetype='text/csv')
    output.headers["Content-Disposition"] = "attachment; filename=Rekap_Alasan_Prabu.csv"
    return output

if __name__ == '__main__':
    app.run(debug=True)