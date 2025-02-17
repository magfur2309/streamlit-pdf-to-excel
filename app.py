import re
import pandas as pd
import pdfplumber
import streamlit as st
from io import BytesIO

def extract_data_from_pdf(pdf_path):
    all_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text(x_tolerance=2, y_tolerance=2) for page in pdf.pages if page.extract_text()])
        st.write("### Debug: Teks dari PDF")
        st.write(text)  # Debugging untuk melihat isi teks

        # Ekstraksi Data Umum
        no_fp_match = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+[\.\d+]*)', text)
        no_fp = no_fp_match.group(1) if no_fp_match else ""
        
        penjual_match = re.search(r'Pengusaha Kena Pajak:\s*Nama\s*:\s*(.*?)\n', text)
        nama_penjual = penjual_match.group(1).strip() if penjual_match else ""
        
        pembeli_match = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*(.*?)\n', text)
        nama_pembeli = pembeli_match.group(1).strip() if pembeli_match else ""
        
        tanggal_match = re.search(r'(\d{1,2} \w+ \d{4})', text)
        tanggal_faktur = tanggal_match.group(1) if tanggal_match else ""
        
        # Ekstraksi Detail Barang
        barang_matches = re.findall(r'(\d+)\s+(\d+)\s+(.*?)\s+Rp ([\d.,]+)', text)
        
        for match in barang_matches:
            nomor = match[0]
            kode = match[1]
            barang = match[2].strip()
            harga = match[3].replace('.', '').replace(',', '.')  # Format angka
            
            all_data.append([no_fp, nama_penjual, nama_pembeli, kode, barang, harga, tanggal_faktur])
    
    return all_data

# Streamlit UI
st.title("Ekstrak Data Faktur Pajak")
uploaded_file = st.file_uploader("Upload Faktur Pajak (PDF)", type=["pdf"])

if uploaded_file:
    with st.spinner("Memproses PDF..."):
        all_data = extract_data_from_pdf(uploaded_file)
        
        if not all_data:
            st.error("Tidak ada data yang ditemukan. Pastikan format faktur sesuai.")
        else:
            df = pd.DataFrame(all_data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Kode", "Barang", "Harga", "Tanggal Faktur"])
            st.dataframe(df)
            
            # Ekspor ke Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Faktur Pajak')
                writer.close()
                processed_data = output.getvalue()
            
            st.download_button(label="Unduh Data sebagai Excel", data=processed_data, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
