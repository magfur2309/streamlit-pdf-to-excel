import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
from datetime import datetime

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF dan memastikan tanggal faktur
    berasal dari halaman terakhir jika terdapat beberapa halaman dalam satu file.
    """
    data = []
    tanggal_faktur = None  # Tanggal faktur akan terus diperbarui hingga halaman terakhir
    nama_penjual = None
    nama_pembeli = None
    no_fp = None
    
    month_mapping = {
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
    }
    
    with pdfplumber.open(pdf_file) as pdf:
        for page_index, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                # Ambil No FP
                no_fp_match = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', text)
                if no_fp_match:
                    no_fp = no_fp_match.group(1)
                
                # Ambil Tanggal Faktur (hanya simpan yang terakhir)
                date_match = re.search(r'\b(\d{1,2})\s+(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+(\d{4})\b', text)
                if date_match:
                    day, month, year = date_match.groups()
                    tanggal_faktur = f"{year}-{month_mapping[month]}-{day.zfill(2)}"  # Selalu diperbarui
                
                # Ambil Nama Penjual tanpa alamat
                penjual_match = re.search(r'Nama\s*:\s*([\w\s\-.,&]+)\nAlamat', text)
                if penjual_match:
                    nama_penjual = penjual_match.group(1).strip()
                
                # Ambil Nama Pembeli tanpa alamat
                pembeli_match = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*([\w\s\-.,&]+)\nAlamat', text)
                if pembeli_match:
                    nama_pembeli = pembeli_match.group(1).strip()
            
            # Ambil data tabel jika ada
            table = page.extract_table()
            if table:
                for row in table:
                    if len(row) >= 4 and row[0].isdigit():  # Pastikan baris valid
                        nama_barang = row[2].replace("\n", " ").strip()
                        
                        # Bersihkan informasi tambahan dari nama barang
                        nama_barang = re.sub(r'Rp [\d.,]+ x [\d.,]+ \w+', '', nama_barang)
                        nama_barang = re.sub(r'Potongan Harga = Rp [\d.,]+', '', nama_barang)
                        nama_barang = re.sub(r'PPnBM \(\d+,?\d*%\) = Rp [\d.,]+', '', nama_barang)
                        
                        harga_qty_info = re.search(r'Rp ([\d.,]+) x ([\d.,]+) (\w+)', row[2])
                        if harga_qty_info:
                            harga = int(float(harga_qty_info.group(1).replace('.', '').replace(',', '.')))
                            qty = int(float(harga_qty_info.group(2).replace('.', '').replace(',', '.')))
                            unit = harga_qty_info.group(3)
                        else:
                            harga, qty, unit = 0, 0, "Unknown"
                        
                        total = harga * qty
                        dpp = total / 1.11  # Menghitung DPP dengan asumsi PPN 11%
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
    
if uploaded_files:
    all_data = []
    
    for uploaded_file in uploaded_files:
        extracted_data = extract_data_from_pdf(uploaded_file)
        if extracted_data:
            for row in extracted_data:
                row.append(uploaded_file.name)  # Tambahkan nama file sebagai identifier
            all_data.extend(extracted_data)
all_tables = []
with pdfplumber.open(pdf_file) as pdf:
    for page in pdf.pages:
        table = page.extract_table()
        if table:
            all_tables.extend(table)

    if all_data:
        df = pd.DataFrame(all_data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Nama Barang", "Harga", "Unit", "QTY", "Total", "DPP", "PPN", "Tanggal Faktur", "Nama File"])

        # Pastikan setiap file tetap memiliki tanggalnya sendiri
        df = df.sort_values(by=["Nama File", "Tanggal Faktur"]).reset_index(drop=True)

        st.write("### Pratinjau Data yang Diekstrak")
        st.dataframe(df.drop(columns=["Nama File"]))  # Tampilkan tanpa kolom Nama File

        # Simpan ke Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=True, sheet_name='Faktur Pajak')
            writer.close()
        output.seek(0)

        st.download_button(label="📥 Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")


