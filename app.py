import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# Konfigurasi Database (Membaca dari Environment Render, atau SQLite untuk tes lokal)
uri = os.environ.get('DATABASE_URL', 'sqlite:///prabu.db')
# Render terkadang memberikan awalan postgres:// yang sudah usang, ini memperbaikinya ke postgresql://
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Konfigurasi Cloudinary
cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key = os.environ.get('CLOUDINARY_API_KEY'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

# Struktur Tabel Database
class Pendaftar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    kelas = db.Column(db.String(20), nullable=False)
    alasan = db.Column(db.Text, nullable=False)
    cv_url = db.Column(db.String(255))
    transkrip_url = db.Column(db.String(255))
    swot_url = db.Column(db.String(255))
    ijazah_url = db.Column(db.String(255))

with app.app_context():
    db.create_all()

@app.route('/')
def form_rekrutmen():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        nama = request.form.get('namaLengkap')
        kelas = request.form.get('kelas')
        alasan = request.form.get('alasan')
        
        # Fungsi untuk mengunggah file ke Cloudinary dan mengembalikan link-nya
        def upload_ke_cloud(file_obj):
            if file_obj and file_obj.filename != '':
                hasil = cloudinary.uploader.upload(file_obj)
                return hasil.get('secure_url')
            return None

        # Proses upload semua file
        cv_url = upload_ke_cloud(request.files.get('cv'))
        transkrip_url = upload_ke_cloud(request.files.get('transkrip'))
        swot_url = upload_ke_cloud(request.files.get('swot'))
        ijazah_url = upload_ke_cloud(request.files.get('ijazah'))

        # Simpan data ke Database PostgreSQL
        pendaftar_baru = Pendaftar(
            nama=nama, kelas=kelas, alasan=alasan,
            cv_url=cv_url, transkrip_url=transkrip_url,
            swot_url=swot_url, ijazah_url=ijazah_url
        )
        db.session.add(pendaftar_baru)
        db.session.commit()

      return render_template('success.html', nama=nama_input)

@app.route('/dashboard')
def dashboard():
    # Mengambil semua data pendaftar
    data_pendaftar = Pendaftar.query.all()
    return render_template('dashboard.html', pendaftar=data_pendaftar)

if __name__ == '__main__':
    app.run(debug=True)
