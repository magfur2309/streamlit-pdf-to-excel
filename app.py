import streamlit as st
import pdfplumber
import re

def extract_items_from_invoice(pdf_path):
    items = []
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    
    # Pola regex untuk menangkap data barang
    item_pattern = re.findall(r'(\d+)\s+([A-Z0-9\s,]+)\s+(\d+[,.]?\d*)\s+Kg\s+Rp ([\d,.]+)', text)
    
    for item in item_pattern:
        items.append({
            "No": item[0],
            "Nama Barang": item[1].strip(),
            "Berat (Kg)": item[2],
            "Harga (Rp)": item[3]
        })
    
    return items

st.title("Ekstraksi Item Barang dari Faktur Pajak PDF")
uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])

if uploaded_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    items = extract_items_from_invoice("temp.pdf")
    
    if items:
        st.write("### Data Barang")
        st.table(items)
    else:
        st.warning("Tidak ada data barang yang dapat diekstrak dari file PDF ini.")
