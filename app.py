import streamlit as st
from PyPDF2 import PdfReader
import pandas as pd

def extract_data_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

    # Proses ekstraksi data dari teks
    lines = text.split('\n')
    data = []
    for line in lines:
        if "|" in line:  # Asumsi data yang relevan mengandung karakter "|"
            parts = line.split("|")
            if len(parts) >= 4:  # Pastikan ada 4 kolom (No., Nama Barang, Harga, dll.)
                no = parts[1].strip()
                nama_barang = parts[2].strip()
                harga = parts[3].strip()
                data.append([no, nama_barang, harga])

    # Buat DataFrame dari data yang diekstrak
    df = pd.DataFrame(data, columns=["No.", "Nama Barang Kena Pajak / Jasa Kena Pajak", "Harga Jual / Penggantian / Uang Muka / Termin (Rp)"])
    return df

def main():
    st.title("Ekstrak Data Faktur PDF")
    st.write("Unggah file PDF faktur untuk mengekstrak data.")

    uploaded_file = st.file_uploader("Pilih file PDF", type="pdf")
    if uploaded_file is not None:
        st.write("File berhasil diunggah!")
        df = extract_data_from_pdf(uploaded_file)
        if not df.empty:
            st.write("Data yang diekstrak:")
            st.dataframe(df)
        else:
            st.write("Tidak ada data yang dapat diekstrak dari file PDF ini.")

if __name__ == "__main__":
    main()
