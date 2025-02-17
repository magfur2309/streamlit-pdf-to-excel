import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
from datetime import datetime

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF dan mengonversinya ke format tabel,
    menangani banyak halaman dan beberapa tabel dalam satu file.
    """
    data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table:
                    if any(row):  # Pastikan baris tidak kosong
                        try:
                            no_fp = row[0] if row[0] else ""
                            nama_penjual = row[1] if row[1] else ""
                            nama_pembeli = row[2] if row[2] else ""
                            barang = row[3] if row[3] else ""
                            harga = int(float(row[4].replace('.', '').replace(',', '.'))) if row[4] else 0
                            unit = row[5] if row[5] else ""
                            qty = int(float(row[6].replace('.', '').replace(',', '.'))) if row[6] else 0
                            total = harga * qty
                            dpp = total / 1.11  # Menghitung DPP dengan asumsi PPN 11%
                            ppn = total - dpp
                            tanggal_faktur = row[7] if row[7] else ""
                            
                            data.append([no_fp, nama_penjual, nama_pembeli, barang.strip(), harga, unit, qty, total, dpp, ppn, tanggal_faktur])
                        except Exception as e:
                            st.error(f"Kesalahan dalam membaca baris: {e}")
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
        df = pd.DataFrame(all_data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Barang", "Harga", "Unit", "QTY", "Total", "DPP", "PPN", "Tanggal Faktur"])
        df.insert(0, "No", range(1, len(df) + 1))  # Tambah kolom No di paling kiri
        
        # Menampilkan pratinjau data
        st.write("### Pratinjau Data yang Diekstrak")
        st.dataframe(df)
        
        # Simpan ke Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Faktur Pajak')
            writer.close()
        output.seek(0)
        
        st.download_button(label="📥 Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
