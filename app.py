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
    
    month_mapping = {
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
    }
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
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
                    
                    no_fp = no_fp.group(1) if no_fp else ""
                    nama_penjual = nama_penjual.group(1).strip() if nama_penjual else ""
                    nama_pembeli = nama_pembeli.group(1).strip() if nama_pembeli else ""
                    
                    # Menangkap informasi barang/jasa secara lebih akurat
                    start_extracting = False
                    barang_list = []
                    for line in text.split("\n"):
                        if "Nama Barang Kena Pajak / Jasa Kena Pajak" in line:
                            start_extracting = True
                            continue
                        
                        if start_extracting:
                            if re.match(r'\d+\s+\d{6}', line):  # Deteksi pola nomor barang
                                barang_list.append(line.split(maxsplit=2)[-1].strip())
                            elif any(keyword in line.lower() for keyword in ["ppn", "total", "jumlah"]):
                                break  # Berhenti saat mencapai bagian perhitungan pajak
                    
                    for barang in barang_list:
                        data.append([faktur_counter, no_fp, nama_penjual, nama_pembeli, barang, tanggal_faktur if tanggal_faktur else "Tidak ditemukan"])
                    
                    faktur_counter += 1  # Naikkan counter jika ada faktur baru
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
        df = pd.DataFrame(all_data, columns=["No", "No FP", "Nama Penjual", "Nama Pembeli", "Barang", "Tanggal Faktur"])
        
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
