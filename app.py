import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF faktur pajak dan mengonversinya ke format tabel.
    """
    data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue  # Lewati halaman kosong
            
            lines = text.split('\n')

            def find_value(key):
                return next((line.split(':')[-1].strip() for line in lines if key in line), None)

            # Cari informasi penting dari faktur
            no_fp = find_value("Kode dan Nomor Seri Faktur Pajak")
            nama_penjual = find_value("Pengusaha Kena Pajak")
            nama_pembeli = find_value("Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak")
            npwp_penjual = find_value("NPWP")
            npwp_pembeli = find_value("NPWP")

            # Ekstrak item barang dan harga
            harga, qty, total, dpp, ppn = None, None, None, None, None
            barang, unit = None, "Unit"
            
            for i, line in enumerate(lines):
                if re.search(r'Rp\s[\d,.]+\sx\s\d+', line):  # Pencarian harga dan qty
                    try:
                        parts = line.replace('Rp', '').replace(',', '').split('x')
                        harga = int(parts[0].strip())
                        qty = int(parts[1].split()[0].strip())
                        total = harga * qty
                        unit = "Bulan" if "Bulan" in line else "Unit"
                    except Exception:
                        harga, qty, total = None, None, None

                if "Dasar Pengenaan Pajak" in line:  # Cari DPP
                    try:
                        dpp = int(lines[i + 1].replace(',', '').strip())
                    except Exception:
                        dpp = None

                if "Jumlah PPN" in line:  # Cari PPN
                    try:
                        ppn = int(lines[i + 1].replace(',', '').strip())
                    except Exception:
                        ppn = None

                if "Nama Barang Kena Pajak / Jasa Kena Pajak" in line:  # Ambil nama barang/jasa
                    barang = lines[i + 1].strip() if i + 1 < len(lines) else None
            
            if no_fp and nama_penjual and nama_pembeli:
                data.append([no_fp, nama_penjual, npwp_penjual, nama_pembeli, npwp_pembeli, barang, harga, unit, qty, total, dpp, ppn])
    
    return data if data else None

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
        df = pd.DataFrame(all_data, columns=["No FP", "Nama Penjual", "NPWP Penjual", "Nama Pembeli", "NPWP Pembeli", "Barang/Jasa", "Harga", "Unit", "QTY", "Total", "DPP", "PPN"])
        
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
        st.error("Gagal mengekstrak data. Pastikan format faktur sesuai atau gunakan OCR jika PDF berbentuk gambar.")
