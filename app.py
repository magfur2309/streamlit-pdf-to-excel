import streamlit as st
import fitz  # PyMuPDF
import re

def extract_data_from_pdf(pdf_file, nomor_urut):
    doc = fitz.open(pdf_file)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    
    # Cari data berdasarkan nomor urut
    pattern = rf"{nomor_urut}\\s+600600\\s+([\s\S]+?)\\n\\n"
    match = re.search(pattern, text)
    
    if match:
        return match.group(1).strip()
    else:
        return "Data tidak ditemukan"

st.title("Pembaca Faktur PDF")

uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])
nomor_urut = st.number_input("Masukkan Nomor Urut", min_value=1, step=1)

if uploaded_file is not None and nomor_urut:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    result = extract_data_from_pdf("temp.pdf", nomor_urut)
    
    st.subheader(f"Data untuk Nomor Urut {nomor_urut}:")
    st.text(result)
