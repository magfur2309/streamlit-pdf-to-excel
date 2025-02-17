import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def extract_data_from_pdf(pdf_file):
    data = []
    nomor_faktur, nama_penjual, nama_pembeli = "", "", ""
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                try:
                    if not nomor_faktur:
                        match = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', text)
                        nomor_faktur = match.group(1) if match else ""
                    
                    if not nama_penjual:
                        match = re.search(r'Pengusaha Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                        nama_penjual = match.group(1).strip() if match else ""
                    
                    if not nama_pembeli:
                        match = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                        nama_pembeli = match.group(1).strip() if match else ""
                    
                    # Menangkap informasi barang per nomor urut
                    items = re.findall(r'(\d+)\s+000000\n([\s\S]+?)\nRp ([\d.,]+) x ([\d.,]+) Piece', text)
                    
                    for item in items:
                        nomor_urut = item[0]
                        barang = item[1].strip()
                        harga = float(item[2].replace('.', '').replace(',', '.'))
                        qty = int(float(item[3].replace('.', '').replace(',', '.')))
                        total = harga * qty
                        
                        data.append([nomor_faktur, nama_penjual, nama_pembeli, nomor_urut, barang, harga, qty, total])
                except Exception as e:
                    st.error(f"Kesalahan saat membaca halaman: {e}")
    return data

# Streamlit UI
st.title("Ekstraksi Faktur Pajak PDF ke Excel")

uploaded_files = st.file_uploader("Upload Faktur Pajak (PDF, bisa lebih dari satu)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    
    for uploaded_file in uploaded_files:
        extracted_data = extract_data_from_pdf(uploaded_file)
        if extracted_data:
            all_data.extend(extracted_data)
    
    if all_data:
        df = pd.DataFrame(all_data, columns=["No Faktur", "Nama Penjual", "Nama Pembeli", "No Urut", "Barang", "Harga", "QTY", "Total"])
        df = df.sort_values(by=["No Faktur", "No Urut"]).reset_index(drop=True)
        
        st.write("### Pratinjau Data yang Diekstrak")
        st.dataframe(df)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Faktur Pajak')
            writer.close()
        output.seek(0)
        
        st.download_button(label="📥 Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
