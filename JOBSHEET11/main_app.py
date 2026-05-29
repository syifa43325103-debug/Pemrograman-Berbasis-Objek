# main_app.py
import streamlit as st
import datetime
import pandas as pd
import locale

# Setup locale untuk format Rupiah
try:
    locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Indonesian_Indonesia.1252')
    except:
        print("Locale id_ID/Indonesian tidak tersedia.")

def format_rp(angka):
    """Format angka ke format Rupiah."""
    try:
        return locale.currency(angka or 0, grouping=True, symbol='Rp ')[:-3]
    except:
        return f"Rp {angka or 0:,.0f}".replace(",", ".")

# Import modul-modul backend
try:
    from model import Transaksi
    from manajer_anggaran import AnggaranHarian
    from konfigurasi import KATEGORI_PENGELUARAN
except ImportError as e:
    st.error(f"Gagal mengimpor modul: {e}. Pastikan semua file .py ada di folder yang sama.")
    st.stop()

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Catatan Pengeluaran",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Inisialisasi AnggaranHarian (Cache agar tidak re-init setiap rerun) ---
@st.cache_resource
def get_anggaran_manager():
    print(">>> STREAMLIT: (Cache Resource) Menginisialisasi AnggaranHarian...")
    return AnggaranHarian()

anggaran = get_anggaran_manager()


# ------------------------------------------------------------------ #
#  HALAMAN 1: Input Transaksi Baru
# ------------------------------------------------------------------ #
def halaman_input(anggaran: AnggaranHarian):
    st.header("➕ Tambah Pengeluaran Baru")

    with st.form("form_transaksi_baru", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            deskripsi = st.text_input("Deskripsi*", placeholder="Contoh: Makan siang di warung")
        with col2:
            kategori = st.selectbox("Kategori*:", KATEGORI_PENGELUARAN, index=0)

        col3, col4 = st.columns([1, 1])
        with col3:
            jumlah = st.number_input(
                "Jumlah (Rp)*:",
                min_value=0.01,
                step=1000.0,
                format="%.0f",
                value=None,
                placeholder="Contoh: 25000"
            )
        with col4:
            tanggal = st.date_input("Tanggal*:", value=datetime.date.today())

        submitted = st.form_submit_button("💾 Simpan Transaksi")

        if submitted:
            if not deskripsi:
                st.warning("⚠️ Deskripsi wajib diisi!", icon="⚠️")
            elif jumlah is None or jumlah <= 0:
                st.warning("⚠️ Jumlah wajib diisi dan harus lebih dari 0!", icon="⚠️")
            else:
                with st.spinner("Menyimpan..."):
                    tx = Transaksi(deskripsi, float(jumlah), kategori, tanggal)
                    if anggaran.tambah_transaksi(tx):
                        st.success(f"✅ Transaksi '{deskripsi}' berhasil disimpan! (ID: {tx.id})", icon="✅")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Gagal menyimpan transaksi.", icon="❌")


# ------------------------------------------------------------------ #
#  HALAMAN 2: Riwayat Transaksi
# ------------------------------------------------------------------ #
def halaman_riwayat(anggaran: AnggaranHarian):
    st.header("📋 Riwayat Transaksi")

    if st.button("🔄 Refresh Riwayat"):
        st.cache_data.clear()
        st.rerun()

    # Ambil data dengan kolom ID untuk keperluan hapus
    with st.spinner("Memuat riwayat..."):
        query = "SELECT id, tanggal, kategori, deskripsi, jumlah FROM transaksi ORDER BY tanggal DESC, id DESC"
        import database as db_module
        df_raw = db_module.get_dataframe(query)

    if df_raw is None or df_raw.empty:
        st.info("ℹ️ Belum ada transaksi. Tambahkan pengeluaran pertama kamu!")
    else:
        # Format tampilan tabel (tanpa kolom jumlah mentah)
        df_tampil = df_raw.copy()
        df_tampil['Jumlah (Rp)'] = df_tampil['jumlah'].map(
            lambda x: f"Rp {x or 0:,.0f}".replace(",", ".")
        )
        df_tampil = df_tampil[['id', 'tanggal', 'kategori', 'deskripsi', 'Jumlah (Rp)']]
        df_tampil.columns = ['ID', 'Tanggal', 'Kategori', 'Deskripsi', 'Jumlah (Rp)']

        st.dataframe(df_tampil, use_container_width=True, hide_index=True)
        st.caption(f"Total {len(df_tampil)} transaksi tercatat.")

        # ── Fitur Hapus Transaksi ── #
        st.divider()
        st.subheader("🗑️ Hapus Transaksi")

        # Ambil daftar ID yang valid dari database
        daftar_id = df_raw['id'].tolist()

        col_input, col_info = st.columns([1, 2])
        with col_input:
            id_hapus = st.number_input(
                "Masukkan ID Transaksi yang ingin dihapus:",
                min_value=1,
                step=1,
                value=None,
                placeholder="Contoh: 3"
            )

        # Tampilkan preview transaksi yang akan dihapus
        if id_hapus is not None:
            id_hapus = int(id_hapus)
            if id_hapus in daftar_id:
                data_target = df_raw[df_raw['id'] == id_hapus].iloc[0]
                with col_info:
                    st.warning(
                        f"⚠️ Transaksi yang akan dihapus:\n\n"
                        f"**ID:** {id_hapus} | "
                        f"**Deskripsi:** {data_target['deskripsi']} | "
                        f"**Jumlah:** Rp {data_target['jumlah']:,.0f} | "
                        f"**Tanggal:** {data_target['tanggal']}"
                    )
            else:
                with col_info:
                    st.error(f"❌ ID {id_hapus} tidak ditemukan di database.")

        # Tombol konfirmasi hapus
        if id_hapus is not None and int(id_hapus) in daftar_id:
            # Simpan state konfirmasi di session_state
            if 'konfirmasi_hapus' not in st.session_state:
                st.session_state.konfirmasi_hapus = False

            col_btn1, col_btn2, _ = st.columns([1, 1, 3])
            with col_btn1:
                if st.button("🗑️ Hapus Transaksi", type="primary"):
                    st.session_state.konfirmasi_hapus = True

            # Tampilkan dialog konfirmasi
            if st.session_state.konfirmasi_hapus:
                st.warning("⚠️ Apakah kamu yakin ingin menghapus transaksi ini? Tindakan ini tidak bisa dibatalkan!")
                col_ya, col_tidak, _ = st.columns([1, 1, 4])
                with col_ya:
                    if st.button("✅ Ya, Hapus!", type="primary"):
                        with st.spinner("Menghapus..."):
                            berhasil = anggaran.hapus_transaksi(int(id_hapus))
                        if berhasil:
                            st.success(f"✅ Transaksi ID {id_hapus} berhasil dihapus!")
                            st.session_state.konfirmasi_hapus = False
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Gagal menghapus transaksi.")
                            st.session_state.konfirmasi_hapus = False
                with col_tidak:
                    if st.button("❌ Batal"):
                        st.session_state.konfirmasi_hapus = False
                        st.rerun()


# ------------------------------------------------------------------ #
#  HALAMAN 3: Ringkasan & Grafik
# ------------------------------------------------------------------ #
def halaman_ringkasan(anggaran: AnggaranHarian):
    st.header("📊 Ringkasan Pengeluaran")

    # Filter periode
    col_filter1, col_filter2 = st.columns([1, 2])
    with col_filter1:
        pilihan_periode = st.selectbox(
            "Filter Periode:",
            ["Semua Waktu", "Hari Ini", "Pilih Tanggal"],
            key="filter_periode"
        )

    tanggal_filter = None
    label_periode = "(Semua Waktu)"

    if pilihan_periode == "Hari Ini":
        tanggal_filter = datetime.date.today()
        label_periode = f"({tanggal_filter.strftime('%d %b %Y')})"
    elif pilihan_periode == "Pilih Tanggal":
        tanggal_filter = st.date_input(
            "Pilih Tanggal:",
            value=datetime.date.today(),
            key="tanggal_pilihan"
        )
        label_periode = f"({tanggal_filter.strftime('%d %b %Y')})"

    # Tampilkan total pengeluaran
    with col_filter2:
        @st.cache_data(ttl=300)
        def hitung_total_cached(tgl_filter):
            return anggaran.hitung_total_pengeluaran(tanggal=tgl_filter)

        total_pengeluaran = hitung_total_cached(tanggal_filter)
        st.metric(
            label=f"💰 Total Pengeluaran {label_periode}",
            value=format_rp(total_pengeluaran)
        )

    st.divider()

    # Tabel & grafik per kategori
    st.subheader(f"Pengeluaran per Kategori {label_periode}")

    @st.cache_data(ttl=300)
    def get_kategori_cached(tgl_filter):
        return anggaran.get_pengeluaran_per_kategori(tanggal=tgl_filter)

    with st.spinner("Memuat ringkasan kategori..."):
        dict_per_kategori = get_kategori_cached(tanggal_filter)

    if not dict_per_kategori:
        st.info("ℹ️ Tidak ada data untuk periode ini.")
    else:
        try:
            data_kategori = [{"Kategori": kat, "Total": jml} for kat, jml in dict_per_kategori.items()]
            df_kategori = (
                pd.DataFrame(data_kategori)
                .sort_values(by="Total", ascending=False)
                .reset_index(drop=True)
            )
            df_kategori['Total (Rp)'] = df_kategori['Total'].apply(format_rp)

            col_kat1, col_kat2 = st.columns(2)
            with col_kat1:
                st.write("📋 Tabel:")
                st.dataframe(
                    df_kategori[['Kategori', 'Total (Rp)']],
                    hide_index=True,
                    use_container_width=True
                )
            with col_kat2:
                st.write("📊 Grafik:")
                st.bar_chart(
                    df_kategori.set_index('Kategori')['Total'],
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"❌ Gagal menampilkan ringkasan: {e}")


# ------------------------------------------------------------------ #
#  FUNGSI UTAMA
# ------------------------------------------------------------------ #
def main():
    st.sidebar.title("💸 Catatan Pengeluaran")
    menu_pilihan = st.sidebar.radio(
        "Pilih Menu:",
        ["➕ Tambah", "📋 Riwayat", "📊 Ringkasan"],
        key="menu_utama"
    )
    st.sidebar.markdown("---")
    st.sidebar.info("Jobsheet 11 - Aplikasi Keuangan OOP")

    manajer_anggaran = get_anggaran_manager()

    if menu_pilihan == "➕ Tambah":
        halaman_input(manajer_anggaran)
    elif menu_pilihan == "📋 Riwayat":
        halaman_riwayat(manajer_anggaran)
    elif menu_pilihan == "📊 Ringkasan":
        halaman_ringkasan(manajer_anggaran)

    st.markdown("---")
    st.caption("Pengembangan Aplikasi Berbasis OOP | Jobsheet 11")


if __name__ == "__main__":
    main()