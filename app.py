import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
from datetime import datetime

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF dan mengonversinya ke format tabel,
    memastikan semua barang dari multi-halaman terbaca dengan akurat.
    """
    data = []
    with pdfplumber.open(pdf_file) as pdf:
        no_fp, nama_penjual, nama_pembeli = "", "", ""
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table:
                    if any(row):  # Pastikan ada data dalam baris
                        try:
                            # Ambil data berdasarkan kolom yang sesuai
                            kode_barang = row[0].strip() if row[0] else ""
                            nama_barang = row[1].strip() if row[1] else ""
                            harga = float(row[2].replace('.', '').replace(',', '.')) if row[2] else 0.0
                            qty = float(row[3].replace('.', '').replace(',', '.')) if row[3] else 0.0
                            unit = row[4].strip() if row[4] else ""
                            total = harga * qty

                            data.append([no_fp, nama_penjual, nama_pembeli, kode_barang, nama_barang, harga, unit, qty, total])
                        except Exception as e:
                            st.error(f"Terjadi kesalahan dalam membaca tabel: {e}")
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
        df = pd.DataFrame(all_data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Kode Barang", "Barang", "Harga", "Unit", "QTY", "Total"])
        
        # Hilangkan baris kosong dan reset index
        df = df[df['Barang'] != ""].reset_index(drop=True)
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
