import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
from datetime import datetime

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF dan mengonversinya ke format tabel,
    memastikan semua barang dari multi-halaman terbaca.
    """
    data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                try:
                    # Menangkap informasi faktur
                    no_fp = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', text)
                    nama_penjual = re.search(r'Pengusaha Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                    nama_pembeli = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                    
                    no_fp = no_fp.group(1) if no_fp else ""
                    nama_penjual = nama_penjual.group(1).strip() if nama_penjual else ""
                    nama_pembeli = nama_pembeli.group(1).strip() if nama_pembeli else ""
                    
                    # Menangkap informasi barang/jasa dengan regex yang lebih fleksibel
                    barang_pattern = re.findall(r'\d+\s+000000\s+([\s\S]*?)\s+Rp\s([\d.,]+)\s+x\s+([\d.,]+)\s+Piece', text)
                    
                    for barang in barang_pattern:
                        nama_barang = barang[0].strip()
                        harga = int(float(barang[1].replace('.', '').replace(',', '.')))
                        qty = int(float(barang[2].replace('.', '').replace(',', '.')))
                        unit = "Piece"
                        total = harga * qty
                        
                        data.append([no_fp, nama_penjual, nama_pembeli, nama_barang, harga, unit, qty, total])
                except Exception as e:
                    st.error(f"Terjadi kesalahan dalam membaca halaman: {e}")
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
