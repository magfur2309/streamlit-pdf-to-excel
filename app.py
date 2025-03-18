import streamlit as st
import pdfplumber
import re

def extract_data_from_pdf(pdf_file):
    extracted_data = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split("\n")
                for line in lines:
                    match = re.match(r"(\d+)\s+(\d{6})\s+([A-Z0-9 ,.\-]+)\s+Rp ([\d,.]+) x ([\d,.]+) Kilogram\s+Potongan Harga = Rp ([\d,.]+)\s+PPnBM \(\d+,?\d*%\) = Rp ([\d,.]+)\s+([\d,.]+)", line)
                    if match:
                        extracted_data.append({
                            "No": match.group(1),
                            "Kode": match.group(2),
                            "Nama Barang": match.group(3),
                            "Harga per Kg": match.group(4),
                            "Berat": match.group(5),
                            "Potongan Harga": match.group(6),
                            "PPnBM": match.group(7),
                            "Total Harga": match.group(8)
                        })
    
    return extracted_data

def main():
    st.title("Sistem Pembacaan Faktur Pajak dari PDF")
    uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])
    
    if uploaded_file is not None:
        data = extract_data_from_pdf(uploaded_file)
        if data:
            st.write("### Data yang Diekstrak:")
            st.table(data)
        else:
            st.warning("Tidak ada data yang dapat diekstrak dari file PDF ini.")

if __name__ == "__main__":
    main()
