import streamlit as st
import PyPDF2
import pandas as pd

def extract_data_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)
    text = ""
    for page_num in range(pdf_reader.numPages):
        page = pdf_reader.getPage(page_num)
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
        st.write("Data yang diekstrak:")
        st.dataframe(df)

if __name__ == "__main__":
    main()
