import streamlit as st
import pdfplumber
import re

def extract_invoice_data(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    
    # Ekstraksi informasi dasar
    faktur_no = re.search(r'Kode dan Nomor Seri Faktur Pajak: (\d+)', text)
    nama_penjual = re.search(r'Nama: ([A-Z\s]+)', text)
    npwp_penjual = re.search(r'NPWP : (\d+)', text)
    nama_pembeli = re.search(r'Nama : ([A-Z\s]+)', text)
    npwp_pembeli = re.search(r'NPWP : (\d+)', text)
    
    return {
        "Nomor Faktur": faktur_no.group(1) if faktur_no else "Tidak ditemukan",
        "Nama Penjual": nama_penjual.group(1) if nama_penjual else "Tidak ditemukan",
        "NPWP Penjual": npwp_penjual.group(1) if npwp_penjual else "Tidak ditemukan",
        "Nama Pembeli": nama_pembeli.group(1) if nama_pembeli else "Tidak ditemukan",
        "NPWP Pembeli": npwp_pembeli.group(1) if npwp_pembeli else "Tidak ditemukan",
    }

st.title("Sistem Pembacaan Faktur Pajak dari PDF")
uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])

if uploaded_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    data = extract_invoice_data("temp.pdf")
    
    st.write("### Hasil Ekstraksi Faktur Pajak")
    for key, value in data.items():
        st.write(f"**{key}:** {value}")
