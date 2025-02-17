import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari faktur pajak PDF, termasuk nama barang sesuai urutan tabel.
    """
    data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                try:
                    # Ekstrak informasi utama
                    no_fp = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', text)
                    nama_penjual = re.search(r'Pengusaha Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                    nama_pembeli = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                    tanggal_faktur = re.search(r'(\d{1,2}) (Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember) (\d{4})', text)
                    
                    no_fp = no_fp.group(1) if no_fp else ""
                    nama_penjual = nama_penjual.group(1).strip() if nama_penjual else ""
                    nama_pembeli = nama_pembeli.group(1).strip() if nama_pembeli else ""
                    
                    month_mapping = {"Januari": "01", "Februari": "02", "Maret": "03", "April": "04", "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08", "September": "09", "Oktober": "10", "November": "11", "Desember": "12"}
                    tanggal_faktur = f"{tanggal_faktur.group(1).zfill(2)}/{month_mapping.get(tanggal_faktur.group(2), '00')}/{tanggal_faktur.group(3)}" if tanggal_faktur else ""
                    
                    # Ekstrak barang/jasa sesuai urutan tabel
                    barang_pattern = re.findall(r'(\d+)\s+000000\s+(.+?)\nRp ([\d.,]+) x ([\d.,]+) ([\w]+)', text)
                    for idx, barang_match in enumerate(barang_pattern, start=1):
                        no, barang, harga, qty, unit = barang_match
                        harga = int(float(harga.replace('.', '').replace(',', '.')))
                        qty = int(float(qty.replace('.', '').replace(',', '.')))
                        total = harga * qty
                        dpp = total / 1.11  # Asumsi PPN 11%
                        ppn = total - dpp
                        
                        data.append([no, no_fp, nama_penjual, nama_pembeli, barang.strip(), harga, unit, qty, total, dpp, ppn, tanggal_faktur])
                except Exception as e:
                    st.error(f"Terjadi kesalahan dalam membaca halaman: {e}")
    return data

# Streamlit UI
st.title("Konversi Faktur Pajak PDF ke Excel")

uploaded_files = st.file_uploader("Upload Faktur Pajak (PDF)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for uploaded_file in uploaded_files:
        extracted_data = extract_data_from_pdf(uploaded_file)
        if extracted_data:
            all_data.extend(extracted_data)
    
    if all_data:
        df = pd.DataFrame(all_data, columns=["No", "No FP", "Nama Penjual", "Nama Pembeli", "Barang", "Harga", "Unit", "QTY", "Total", "DPP", "PPN", "Tanggal Faktur"])
        df.index = df.index + 1  # Mulai index dari 1
        st.dataframe(df)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Faktur Pajak')
            writer.close()
        output.seek(0)
        
        st.download_button(label="📥 Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
