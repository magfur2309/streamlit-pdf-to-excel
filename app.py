import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO

def extract_data_from_pdf(pdf_file):
    extracted_data = []
    header_found = False
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table:
                    if any("Nama Barang Kena Pajak" in str(cell) for cell in row if cell):
                        header_found = True
                        continue  # Lewati baris header
                    
                    if header_found and len(row) >= 2:
                        no_urut = row[0].strip() if row[0] else ""
                        nama_barang = row[1].strip() if row[1] else ""
                        extracted_data.append([no_urut, nama_barang])
    
    return extracted_data

def generate_download_link(df):
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output

def main():
    st.title("Invoice Report Generator")
    
    uploaded_file = st.file_uploader("Upload Faktur Pajak (PDF)", type=["pdf"])
    
    if uploaded_file:
        try:
            with st.spinner("Mengekstrak data..."):
                data = extract_data_from_pdf(uploaded_file)
                df = pd.DataFrame(data, columns=["No. Urut", "Nama Barang"])
                
                if df.empty:
                    st.warning("Tidak ada data yang diekstrak. Pastikan format tabel dalam PDF sudah benar.")
                else:
                    st.write("### Hasil Ekstraksi Data")
                    st.dataframe(df)
                    
                    csv = generate_download_link(df)
                    st.download_button("Download Laporan CSV", csv, "laporan_invoice.csv", "text/csv")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat ekstraksi: {e}")

if __name__ == "__main__":
    main()
