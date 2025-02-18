import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF dan mengonversinya ke format tabel,
    memastikan nomor urut faktur sesuai dengan yang ada di PDF.
    """
    data = []
    faktur_counter = 1  # Menjaga urutan nomor faktur
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
                    # Mencari tanggal faktur di halaman
                    match_tanggal = re.search(r'(\d{1,2})\s*(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s*(\d{4})', text)
                    if match_tanggal:
                        day, month, year = match_tanggal.groups()
                        tanggal_faktur = f"{day.zfill(2)}/{month_mapping.get(month, '00')}/{year}"
                    
                    no_fp_match = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', text)
                    nama_penjual_match = re.search(r'Pengusaha Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                    nama_pembeli_match = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                    
                    no_fp = no_fp_match.group(1) if no_fp_match else ""
                    nama_penjual = nama_penjual_match.group(1).strip() if nama_penjual_match else ""
                    nama_pembeli = nama_pembeli_match.group(1).strip() if nama_pembeli_match else ""
                    
                    # Menangkap informasi barang/jasa
                    barang_pattern = re.findall(r'(.*?)\s+Rp ([\d.,]+) x ([\d.,]+) (\w+)', text)
                    for barang_match in barang_pattern:
                        barang, harga, qty, unit = barang_match
                        harga = int(float(harga.replace('.', '').replace(',', '.')))
                        qty = int(float(qty.replace('.', '').replace(',', '.')))
                        total = harga * qty
                        dpp = total / 1.11  # Menghitung DPP dengan PPN 11%
                        ppn = total - dpp
                        
                        data.append([faktur_counter, no_fp, nama_penjual, nama_pembeli, barang.strip(), harga, unit, qty, total, dpp, ppn, tanggal_faktur or "Tidak ditemukan"])
                    
                    if no_fp:  # Hanya naikkan faktur_counter jika ada faktur baru
                        faktur_counter += 1
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
        df = pd.DataFrame(all_data, columns=["No", "No FP", "Nama Penjual", "Nama Pembeli", "Barang", "Harga", "Unit", "QTY", "Total", "DPP", "PPN", "Tanggal Faktur"])
        
        # Hapus baris dengan barang kosong dan reset index
        df = df[df['Barang'] != ""].reset_index(drop=True)
        df.index = df.index + 1  # Memastikan nomor urut mulai dari 1
        
        # Urutkan DataFrame berdasarkan "No"
        df = df.sort_values(by=["No"]).reset_index(drop=True)
        df.index = df.index + 1
        
        # Tampilkan pratinjau data
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
