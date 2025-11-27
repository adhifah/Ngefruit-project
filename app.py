from flask import Flask, render_template, request, redirect
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import uuid
import json

load_dotenv()

app = Flask(__name__)

# ==============================
# GOOGLE SHEET SETUP
# ==============================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
if isinstance(google_creds_json, str):
    google_creds_dict = json.loads(google_creds_json)
else:
    google_creds_dict = google_creds_json


creds = ServiceAccountCredentials.from_json_keyfile_dict(
    google_creds_dict,
    scope
)

client = gspread.authorize(creds)

sheet = client.open("Ngefruit Orders").sheet1

# ==============================
# LOCAL UPLOAD SETTINGS
# ==============================
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def save_local_file(file):
    """Simpan bukti transfer ke folder static/uploads & return public URL"""
    if not file:
        return ""

    ext = file.filename.rsplit(".", 1)[-1]
    filename = f"bukti_{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)

    link = f"/static/uploads/{filename}"
    return link


# ==============================
# DATA PRODUK
# ==============================
produk = {
    "buah-potong": {
        "nama": "Buah Potong Segar",
        "harga": 15000,
        "deskripsi": "Buah potong segar dengan kualitas pilihan, dipotong setiap hari untuk menjaga rasa manis alami dan kesegarannya. Cocok sebagai camilan sehat kapan saja!",
        "kandungangizi": "Vitamin A, Vitamin C, Serat tinggi, Antioksidan, Air yang tinggi",
        "ingredients": "Apel, Melon, Anggur, Semangka, Nanas, Mangga",
        "manfaat": "Membantu menjaga daya tahan tubuh, Melancarkan pencernaan, Membantu hidrasi tubuh, Baik untuk kulit, Rendah kalori, Cocok untuk diet",
        "gambar": "buah-potong.png"
    },
    "sando": {
        "nama": "Fruit Sandwich",
        "harga": 18000,
        "deskripsi": "Roti lembut ala Jepang berisi potongan buah segar dan krim yang ringan. Rasanya manis, creamy, dan segar. Cocok untuk sarapan atau camilan manis yang sehat.",
        "kandungangizi": "Karbohidrat dari roti, Vitamin C & antioksidan dari buah, Kalsium & Protein dari whipped cream, Lemak baik",
        "ingredients": "Roti gandum, whipped cream, Buah segar (Strawberry, mangga, anggur)",
        "manfaat": "Memberikan energi cepat untuk beraktivitas, Baik untuk mood boster, Mengandung vitamin dan serat dari buah segar, Cocok dijadikan menu sarapan ringan yang sehat",
        "gambar": "sando.png"
    },
    "jus-buah": {
        "nama": "Jus Buah Premium",
        "harga": 13000,
        "deskripsi": "Jus buah segar dibuat dari 100% buah asli tanpa tambahan pengawet. Rasanya segar, manis alami, dan menyehatkan.",
        "kandungangizi": "Vitamin C tinggi, Vitamin A dan B kompleks, Serat larut, Antioksidan",
        "ingredients": "150-200 gr buah segar, Sedikit air/es batu, Madu (opsional)",
        "manfaat": "Menjaga imunitas, Menjaga Kesehatan Kulit, Mengurangi rasa lelah, Baik untuk detoks tubuh",
        "gambar": "jus-buah.png"
    },
    "salad-buah": {
        "nama": "Salad Buah Yogurt",
        "harga": 17000,
        "deskripsi": "Perpaduan buah segar dengan dressing yoghurt/keju pilihan. Segar, creamy, dan kaya nutrisi.",
        "kandungangizi": "Serat tinggi, Vitamin C,A dan K, Probiotik, Kalsium",
        "ingredients": "Buah segar (apel, anggur, melon, stroberi), Dressing yoghurt/keju, Topping (keju, granola, madu)",
        "manfaat": "Melancarkan metabolisme, Meningkatkan kesehatan pencernaan, Menjaga daya tahan tubuh",
        "gambar": "salad-buah.png"
    }
}


@app.route("/")
def home():
    return render_template("index.html", produk=produk)


@app.route("/produk")
def list_produk():
    return render_template("produk.html", produk=produk)


@app.route("/produk/<id>")
def detail_produk(id):
    return render_template("detail.html", item=produk[id])


# ==============================
# ORDER — DENGAN PEMBAYARAN + BUKTI TF
# ==============================
@app.route("/order", methods=["POST"])
def order():
    tanggal = request.form["tanggal"]
    nama = request.form["nama"]
    produk_pilihan = request.form["produk"]
    buah = request.form.get("buah", "")
    gula = request.form.get("gula", "")
    jumlah = int(request.form["jumlah"])
    nohp = request.form["nohp"]
    catatan = request.form.get("catatan", "")

    pembayaran = request.form.get("pembayaran", "")
    bukti_file = request.files.get("bukti")

    # Hitung harga & total
    harga_satuan = produk[produk_pilihan]["harga"]
    total_harga = harga_satuan * jumlah

    # Simpan file lokal
    buktitf_link = save_local_file(bukti_file) if bukti_file else ""

    # Kirim ke Google Sheet
    sheet.append_row([
        tanggal,
        nama,
        produk_pilihan,
        gula,
        buah,
        jumlah,
        nohp,
        catatan,
        pembayaran,
        buktitf_link
    ])

    # Kirim ke halaman sukses
    return render_template("order_success.html",
                           nama=nama,
                           produk_id=produk_pilihan,
                           produk_nama=produk[produk_pilihan]["nama"],
                           jumlah=jumlah,
                           harga=harga_satuan,
                           total=total_harga,
                           tanggal=tanggal,
                           nohp=nohp,
                           pembayaran=pembayaran,
                           bukti=buktitf_link)


@app.route("/order", methods=["GET"])
def order_get():
    return redirect("/")
if __name__ == "__main__":
    app.run()