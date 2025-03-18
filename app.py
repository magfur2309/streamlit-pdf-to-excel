import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re  # Untuk pencarian pola teks

# Fungsi untuk mengekstrak teks dari PDF
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(pdf_file)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

# Fungsi untuk mengekstrak Nomor Faktur Pajak dari teks
def extract_no_fp(text):
    match = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*([\d]+)', text)
    if match:
        return match.group(1)
    return "Tidak ditemukan"

# Fungsi untuk mengekstrak Nama Barang dari tabel
def extract_nama_barang(text):
    lines = text.split("\n")
    nama_barang_list = []
    start_extracting = False

    for line in lines:
        if "Nama Barang Kena Pajak / Jasa Kena Pajak" in line:
            start_extracting = True  # Mulai mengambil data setelah menemukan header ini
            continue
        
        if start_extracting:
            if not line.strip():  # Jika menemukan baris kosong, berhenti mengambil data
                break
            nama_barang_list.append(line.strip())  # Tambahkan nama barang ke list

    return nama_barang_list

st.title("Ekstraksi Faktur Pajak dari PDF")

uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])

if uploaded_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    extracted_text = extract_text_from_pdf("temp.pdf")

    # Ambil Nomor Faktur Pajak
    no_fp = extract_no_fp(extracted_text)
    st.write(f"**Nomor Faktur Pajak yang Ditemukan:** {no_fp}")

    # Ambil Nama Barang Kena Pajak
    nama_barang_list = extract_nama_barang(extracted_text)

    if nama_barang_list:
        st.subheader("Daftar Nama Barang Kena Pajak:")
        df = pd.DataFrame({"No FP": no_fp, "Nama Barang": nama_barang_list})
        st.dataframe(df)  # Menampilkan tabel di Streamlit
        st.download_button("Unduh Data sebagai Excel", df.to_csv(index=False), "data.csv", "text/csv")
    else:
        st.warning("Tidak ada data barang yang ditemukan dalam PDF.")
