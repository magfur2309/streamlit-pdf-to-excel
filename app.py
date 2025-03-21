import streamlit as st
import pandas as pd
import pdfplumber
import re
from io import BytesIO

def extract_data_from_pdf(pdf_file):
    extracted_data = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for line in lines:
                    # Perbaikan regex untuk menangkap berbagai pola data
                    match = re.match(r"(\d+)\s+[\d.,]+\s+(.+)", line)
                    if match:
                        no_urut = match.group(1)
                        nama_barang = match.group(2)
                        extracted_data.append([no_urut, nama_barang])
                    else:
                        # Jika regex gagal, coba metode split manual
                        parts = line.split()
                        if len(parts) > 1 and parts[0].isdigit():
                            no_urut = parts[0]
                            nama_barang = " ".join(parts[1:])
                            extracted_data.append([no_urut, nama_barang])
    
    return extracted_data

def generate_download_link(df):
    output = BytesIO()
    df.to_csv(output, index=False, encoding="utf-8-sig")  # Memastikan kompatibilitas dengan Excel
    output.seek(0)
    return output

def main():
    st.title("Invoice Report Generator")
    
    uploaded_file = st.file_uploader("Upload Faktur Pajak (PDF)", type=["pdf"])
    
    if uploaded_file:
        with st.spinner("Mengekstrak data..."):
            data = extract_data_from_pdf(uploaded_file)
            if data:
                df = pd.DataFrame(data, columns=["No. Urut", "Nama Barang"])
                st.write("### Hasil Ekstraksi Data")
                st.dataframe(df)
                
                csv = generate_download_link(df)
                st.download_button("Download Laporan CSV", csv, "laporan_invoice.csv", "text/csv")
            else:
                st.error("Tidak ada data yang berhasil diekstrak. Periksa format PDF Anda.")

if __name__ == "__main__":
    main()
