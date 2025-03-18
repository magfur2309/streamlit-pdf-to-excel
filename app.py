import streamlit as st
import fitz  # PyMuPDF
import re

def extract_invoice_data(pdf_file, item_number):
    doc = fitz.open(streamlit_file)
    extracted_text = ""
    for page in doc:
        extracted_text += page.get_text("text") + "\n"
    
    pattern = rf"{item_number}.*?\n.*?\n.*?SJ: (.*?), Tanggal: (.*?)\nRp ([\d,.]+) x ([\d,.]+) Kilogram\nPotongan Harga = Rp ([\d,.]+)\nPPnBM \(.*?\) = Rp ([\d,.]+)\n([\d,.]+)"
    
    match = re.search(pattern, extracted_text, re.DOTALL)
    if match:
        return {
            "Surat Jalan (SJ)": match.group(1),
            "Tanggal": match.group(2),
            "Harga per Kilogram": match.group(3),
            "Berat": match.group(4),
            "Potongan Harga": match.group(5),
            "PPnBM": match.group(6),
            "Total Harga": match.group(7),
        }
    return None

st.title("Ekstraksi Data Faktur Pajak")

uploaded_file = st.file_uploader("Upload file PDF", type="pdf")
item_number = st.text_input("Masukkan nomor item (contoh: 33)")

if uploaded_file and item_number:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    result = extract_invoice_data("temp.pdf", item_number)
    
    if result:
        st.write("### Hasil Ekstraksi:")
        st.json(result)
    else:
        st.error("Data tidak ditemukan, coba nomor lain.")
