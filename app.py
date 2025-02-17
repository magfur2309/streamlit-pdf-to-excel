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
    faktur_counter = 1  # Untuk menjaga urutan nomor faktur
    tanggal_faktur = None  # Menyimpan tanggal faktur jika ada di halaman berikutnya
    last_valid_data = None  # Menyimpan data dari halaman pertama jika halaman berikutnya kosong
    
    month_mapping = {
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
    }
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            page_data = []
            if text:
                try:
                    # Mencari tanggal faktur di setiap halaman
                    match_tanggal = re.search(r'([0-9]{1,2})\s*(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s*([0-9]{4})', text)
                    if match_tanggal:
                        day, month, year = match_tanggal.groups()
                        tanggal_faktur = f"{day.zfill(2)}/{month_mapping.get(month, '00')}/{year}"
                    
                    no_fp = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', text)
                    nama_penjual = re.search(r'Pengusaha Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                    nama_pembeli = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                    
                    no_fp = no_fp.group(1) if no_fp else "Tidak ditemukan"
                    nama_penjual = nama_penjual.group(1).strip() if nama_penjual else "Tidak ditemukan"
                    nama_pembeli = nama_pembeli.group(1).strip() if nama_pembeli else "Tidak ditemukan"
                    
                    # Menangkap informasi barang/jasa dengan berbagai format harga dan qty
                    barang_pattern = re.findall(r'(.*?)\s+Rp ([\d.,]+) x ([\d.,]+) (\w+)', text)
                    if barang_pattern:
                        for barang_match in barang_pattern:
                            barang, harga, qty, unit = barang_match
                            harga = int(float(harga.replace('.', '').replace(',', '.')))
                            qty = int(float(qty.replace('.', '').replace(',', '.')))
                            total = harga * qty
                            dpp = total / 1.11  # Menghitung DPP dengan asumsi PPN 11%
                            ppn = total - dpp
                            
                            page_data.append([faktur_counter, no_fp, nama_penjual, nama_pembeli, barang.strip(), harga, unit, qty, total, dpp, ppn, tanggal_faktur if tanggal_faktur else "Tidak ditemukan"])
                    else:
                        page_data.append([faktur_counter, no_fp, nama_penjual, nama_pembeli, "Tidak ditemukan", 0, "", 0, 0, 0, 0, tanggal_faktur if tanggal_faktur else "Tidak ditemukan"])
                    
                    if page_data:
                        last_valid_data = page_data  # Simpan data yang valid dari halaman pertama
                        data.extend(page_data)
                        faktur_counter += 1
                except Exception as e:
                    st.error(f"Terjadi kesalahan dalam membaca halaman: {e}")
            else:
                if last_valid_data:
                    data.extend(last_valid_data)  # Gunakan data halaman pertama jika halaman berikutnya kosong
    
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
        df = pd.DataFrame(all_data, columns=["No", "No FP", "Nama Penjual", "Nama Pembeli", "Barang", "Harga", "Unit", "QTY", "Total", "DPP", "PPN", "Tanggal Faktur"])
        
        df = df[df['Barang'] != ""].reset_index(drop=True)
        df['No'] = range(1, len(df) + 1)  # Pastikan nomor urut sesuai dengan jumlah faktur
        
        # Mengisi kolom "No FP", "Nama Penjual", dan "Nama Pembeli" dari baris kedua dengan data baris pertama jika kosong
        if not df.empty:
            first_no_fp = df.loc[0, "No FP"]
            first_nama_penjual = df.loc[0, "Nama Penjual"]
            first_nama_pembeli = df.loc[0, "Nama Pembeli"]
            
            df.loc[1:, "No FP"] = df.loc[1:, "No FP"].replace("Tidak ditemukan", first_no_fp)
            df.loc[1:, "Nama Penjual"] = df.loc[1:, "Nama Penjual"].replace("Tidak ditemukan", first_nama_penjual)
            df.loc[1:, "Nama Pembeli"] = df.loc[1:, "Nama Pembeli"].replace("Tidak ditemukan", first_nama_pembeli)
        
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
