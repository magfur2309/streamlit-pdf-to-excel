import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
from datetime import datetime

def parse_number(text):
    """Fungsi untuk mengubah format angka dengan titik dan koma menjadi float/int"""
    if text:
        try:
            return int(float(text.replace(".", "").replace(",", ".")))
        except ValueError:
            return 0
    return 0

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF dan mengonversinya ke format tabel.
    """
    data = []
    with pdfplumber.open(pdf_file) as pdf:
        print(f"Total halaman: {len(pdf.pages)}")
        for idx, page in enumerate(pdf.pages):
            text = page.extract_text()
            print(f"Halaman {idx + 1}:\n{text}\n")  # Debugging
            if text:
                try:
                    # Debugging: Cetak teks halaman
                    st.text(f"Teks Halaman {idx + 1}:\n{text}")
                    
                    # Menangkap informasi faktur
                    no_fp = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', text)
                    nama_penjual = re.search(r'Pengusaha Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                    nama_pembeli = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                    barang_section = re.findall(r'\d+\s+\d+\s+([\w\s\-/]+)\s+Rp ([\d.,]+) x ([\d.,]+) Piece', text)
                    
                    no_fp = no_fp.group(1) if no_fp else "Tidak ditemukan"
                    nama_penjual = nama_penjual.group(1).strip() if nama_penjual else "Tidak ditemukan"
                    nama_pembeli = nama_pembeli.group(1).strip() if nama_pembeli else "Tidak ditemukan"
                    
                    for barang, harga, qty in barang_section:
                        harga = parse_number(harga)
                        qty = parse_number(qty)
                        total = harga * qty
                        unit = "Piece"
                        print(f"Barang: {barang.strip()}, Harga: {harga}, QTY: {qty}, Total: {total}")  # Debugging
                        data.append([no_fp, nama_penjual, nama_pembeli, barang.strip(), harga, unit, qty, total])
                except Exception as e:
                    st.error(f"Terjadi kesalahan dalam membaca halaman {idx + 1}: {e}")
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
        df = pd.DataFrame(all_data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Barang", "Harga", "Unit", "QTY", "Total"])
        
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
