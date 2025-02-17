import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
from datetime import datetime

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF dan mengonversinya ke format tabel.
    """
    data = []
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    try:
                        # Menangkap informasi faktur
                        no_fp = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', text)
                        nama_penjual = re.search(r'Pengusaha Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                        nama_pembeli = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                        
                        no_fp = no_fp.group(1) if no_fp else "Tidak ditemukan"
                        nama_penjual = nama_penjual.group(1).strip() if nama_penjual else "Tidak ditemukan"
                        nama_pembeli = nama_pembeli.group(1).strip() if nama_pembeli else "Tidak ditemukan"
                        
                        # Menangkap semua barang/jasa
                        barang_matches = re.findall(r'(\d+)\s+\d+\s+([\w\s]+)\s+Rp ([\d.,]+) x ([\d.,]+) ([\w]+)', text)
                        
                        for match in barang_matches:
                            kode, barang, harga, qty, unit = match
                            harga = int(float(harga.replace('.', '').replace(',', '.')))
                            qty = int(float(qty.replace('.', '').replace(',', '.')))
                            total = harga * qty
                            
                            # Menangkap data tambahan
                            potongan_harga = re.search(r'Potongan Harga = Rp ([\d.,]+)', text)
                            ppnbm = re.search(r'PPnBM \(0,00%\) = Rp ([\d.,]+)', text)
                            dpp = re.search(r'Dasar Pengenaan Pajak\s*([\d.,]+)', text)
                            ppn = re.search(r'Jumlah PPN \(Pajak Pertambahan Nilai\)\s*([\d.,]+)', text)
                            tanggal_faktur = re.search(r'KOTA .+, (\d{1,2}) (\w+) (\d{4})', text)
                            
                            potongan_harga = int(float(potongan_harga.group(1).replace('.', '').replace(',', '.'))) if potongan_harga else 0
                            ppnbm = int(float(ppnbm.group(1).replace('.', '').replace(',', '.'))) if ppnbm else 0
                            dpp = int(float(dpp.group(1).replace('.', '').replace(',', '.'))) if dpp else 0
                            ppn = int(float(ppn.group(1).replace('.', '').replace(',', '.'))) if ppn else 0
                            
                            # Konversi format tanggal ke angka (dd/mm/yyyy)
                            if tanggal_faktur:
                                day, month, year = tanggal_faktur.groups()
                                month_mapping = {
                                    "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
                                    "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
                                    "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
                                }
                                tanggal_faktur = f"{day.zfill(2)}/{month_mapping.get(month, '00')}/{year}"
                            else:
                                tanggal_faktur = "Tidak ditemukan"
                            
                            data.append([no_fp, nama_penjual, nama_pembeli, barang.strip(), harga, unit, qty, total, potongan_harga, ppnbm, dpp, ppn, tanggal_faktur])
                    except Exception as e:
                        st.warning(f"Terjadi kesalahan dalam membaca halaman: {e}")
    except Exception as e:
        st.error(f"Gagal membuka file PDF: {e}")
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
        df = pd.DataFrame(all_data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Barang", "Harga", "Unit", "QTY", "Total", "Potongan Harga", "PPnBM", "DPP", "PPN", "Tanggal Faktur"])
        
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
        st.warning("Gagal mengekstrak data. Pastikan format faktur sesuai atau gunakan PDF dengan teks yang dapat disalin.")
