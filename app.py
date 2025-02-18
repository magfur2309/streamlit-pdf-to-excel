import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
from datetime import datetime

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari PDF, menangani banyak halaman,
    menggabungkan tabel dari seluruh halaman agar urutannya sesuai dengan PDF.
    """
    data = []
    all_tables = []  # Menyimpan semua tabel dari semua halaman
    no_fp, nama_penjual, nama_pembeli, tanggal_faktur = None, None, None, None
    
    month_mapping = {
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
    }
    
    with pdfplumber.open(pdf_file) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            
            if text:
                # Ambil No FP
                no_fp_match = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', text)
                if no_fp_match:
                    no_fp = no_fp_match.group(1)
                
                # Ambil Tanggal Faktur dari Halaman Terakhir
                date_match = re.search(r'\b(\d{1,2})\s+(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+(\d{4})\b', text)
                if date_match:
                    day, month, year = date_match.groups()
                    tanggal_faktur = f"{year}-{month_mapping[month]}-{day.zfill(2)}"
                
                # Ambil Nama Penjual
                penjual_match = re.search(r'Nama\s*:\s*([\w\s\-.,&]+)\nAlamat', text)
                if penjual_match:
                    nama_penjual = penjual_match.group(1).strip()
                
                # Ambil Nama Pembeli
                pembeli_match = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*([\w\s\-.,&]+)\nAlamat', text)
                if pembeli_match:
                    nama_pembeli = pembeli_match.group(1).strip()
            
            # Ambil semua tabel
            table = page.extract_table()
            if table:
                all_tables.extend(table)  # Simpan semua tabel dalam urutan yang benar

        # Proses tabel setelah semua halaman diproses
        for row in all_tables:
            if len(row) >= 4 and row[0].isdigit():  # Pastikan hanya memproses baris dengan angka di kolom pertama
                nama_barang = row[2].replace("\n", " ").strip()
                nama_barang = re.sub(r'Rp [\d.,]+ x [\d.,]+ \w+', '', nama_barang)
                nama_barang = re.sub(r'Potongan Harga = Rp [\d.,]+', '', nama_barang)
                nama_barang = re.sub(r'PPnBM \(\d+,?\d*%\) = Rp [\d.,]+', '', nama_barang)
                
                # Ekstrak harga dan quantity
                harga_qty_info = re.search(r'Rp ([\d.,]+) x ([\d.,]+) (\w+)', row[2])
                if harga_qty_info:
                    harga = int(float(harga_qty_info.group(1).replace('.', '').replace(',', '.')))
                    qty = int(float(harga_qty_info.group(2).replace('.', '').replace(',', '.')))
                    unit = harga_qty_info.group(3)
                else:
                    harga, qty, unit = 0, 0, "Unknown"
                
                total = harga * qty
                dpp = total / 1.11  # Asumsi PPN 11%
                ppn = total - dpp
                
                data.append([
                    no_fp if no_fp else "Tidak ditemukan", 
                    nama_penjual if nama_penjual else "Tidak ditemukan", 
                    nama_pembeli if nama_pembeli else "Tidak ditemukan", 
                    nama_barang, harga, unit, qty, total, dpp, ppn, 
                    tanggal_faktur if tanggal_faktur else "Tidak ditemukan"
                ])
    
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
        df = pd.DataFrame(all_data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Nama Barang", "Harga", "Unit", "QTY", "Total", "DPP", "PPN", "Tanggal Faktur"])
        
        df = df[df['Nama Barang'] != ""].reset_index(drop=True)
        df.index = df.index + 1  # Mulai index dari 1
        
        # Pastikan semua baris memiliki tanggal faktur dari halaman terakhir
        if "Tidak ditemukan" in df["Tanggal Faktur"].values and df["Tanggal Faktur"].iloc[-1] != "Tidak ditemukan":
            df["Tanggal Faktur"] = df["Tanggal Faktur"].replace("Tidak ditemukan", df["Tanggal Faktur"].iloc[-1])
        
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
