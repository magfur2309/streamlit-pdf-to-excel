import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
from datetime import datetime

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF dan mengonversinya ke format tabel,
    menangani banyak halaman dan membaca hanya baris pertama dari setiap kolom "Nama Barang Kena Pajak / Jasa Kena Pajak".
    """
    data = []
    faktur_counter = 1  # Untuk menjaga urutan nomor faktur
    tanggal_faktur = None  # Menyimpan tanggal faktur jika ada di halaman berikutnya

    month_mapping = {
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
    }

    with pdfplumber.open(pdf_file) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table in tables:
                if table and len(table) > 1:  # Pastikan tabel memiliki data
                    header = table[0]
                    first_row = table[1]  # Ambil hanya baris pertama dari tabel
                    nama_barang_index = None

                    # Cari indeks kolom Nama Barang
                    for i, col_name in enumerate(header):
                        if col_name and "Barang" in col_name:
                            nama_barang_index = i
                            break

                    # Jika ditemukan, simpan hanya baris pertama
                    if nama_barang_index is not None and nama_barang_index < len(first_row):
                        nama_barang = first_row[nama_barang_index].strip()
                        harga = first_row[nama_barang_index + 1] if nama_barang_index + 1 < len(first_row) else ""
                        qty = first_row[nama_barang_index + 2] if nama_barang_index + 2 < len(first_row) else ""
                        total = first_row[nama_barang_index + 3] if nama_barang_index + 3 < len(first_row) else ""

                        data.append([faktur_counter, f"Halaman {page_number}", nama_barang, harga, qty, total])

            faktur_counter += 1  # Naikkan counter jika ada faktur baru

    return data

# Streamlit UI
st.title("Konversi Faktur Pajak PDF ke Excel")

uploaded_files = st.file_uploader("Upload Faktur Pajak (PDF, bisa lebih dari satu)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_data = []

    for uploaded_file in uploaded_files:
        extracted_data = extract_data_from_pdf(uploaded_file)
        if extracted_data:
            all_data.extend(extracted_data)

    if all_data:
        df = pd.DataFrame(all_data, columns=["No", "Halaman", "Nama Barang", "Harga", "QTY", "Total"])

        df = df[df['Nama Barang'] != ""].reset_index(drop=True)
        df.index = df.index + 1  # Mulai index dari 1

        # Menampilkan pratinjau data
        st.write("### Pratinjau Data yang Diekstrak")
        st.dataframe(df)

        # Simpan ke Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=True, sheet_name='Faktur Pajak')
            writer.close()
        output.seek(0)

        st.download_button(label="📥 Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
