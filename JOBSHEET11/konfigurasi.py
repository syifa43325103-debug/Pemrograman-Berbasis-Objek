# konfigurasi.py
import os

# Baris ini gunanya untuk mencari tahu di folder mana file ini disimpan secara otomatis
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ini nama file database tempat menyimpan data pengeluaran kita nanti
NAMA_DB = 'pengeluaran_harian.db'

# Ini menggabungkan folder utama dan nama database agar komputer tahu lokasi pastinya
DB_PATH = os.path.join(BASE_DIR, NAMA_DB)

# Daftar pilihan kategori pengeluaran yang akan muncul di aplikasi web
KATEGORI_PENGELUARAN = ["Makanan", "Transportasi", "Hiburan", "Tagihan", "Belanja", "Kesehatan", "Pendidikan", "Lainnya"]

# Kategori otomatis jika pengguna tidak memilih kategori apa pun
KATEGORI_DEFAULT = "Lainnya"