import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF dan hanya mengambil tabel dengan header 
    'Nama Barang Kena Pajak / Jasa Kena Pajak'
    """
    data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                try:
                    # Cari posisi tabel yang berisi "Nama Barang Kena Pajak / Jasa Kena Pajak"
                    table_start = re.search(r'Nama Barang Kena Pajak / Jasa Kena Pajak', text)
                    if table_start:
                        barang_text = text[table_start.end():].strip()
                        barang_lines = barang_text.split('\n')
                        
                        # Ambil hanya baris pertama yang berisi deskripsi barang
                        barang = ""
                        for line in barang_lines:
                            if re.search(r'Rp\s[\d.,]+', line):  
                                break  # Berhenti jika sudah mencapai harga
                            barang = line.strip()
                            break  # Hanya ambil satu baris pertama

                        # Simpan hanya jika ada data barang yang valid
                        if barang:
                            data.append([barang])
                except Exception as e:
                    st.error(f"Terjadi kesalahan dalam membaca halaman: {e}")
    return data

# Streamlit UI
st.title("Ekstraksi Data Faktur Pajak ke Excel")

uploaded_files = st.file_uploader("Upload Faktur Pajak (PDF, bisa lebih dari satu)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    
    for uploaded_file in uploaded_files:
        extracted_data = extract_data_from_pdf(uploaded_file)
        if extracted_data:
            all_data.extend(extracted_data)
    
    if all_data:
        df = pd.DataFrame(all_data, columns=["Nama Barang / Jasa"])
        
        # Hilangkan baris kosong dan reset index
        df = df[df['Nama Barang / Jasa'] != ""].reset_index(drop=True)
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
        
        st.download_button(label="💾 Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
