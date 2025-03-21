import streamlit as st
import pandas as pd
import pdfplumber
import re
from io import BytesIO

def extract_data_from_pdf(pdf_file):
    extracted_data = []
    current_entry = None  # Untuk menyimpan entri sementara

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for line in lines:
                    match = re.match(r"^(\d+)\s+Rp ([\d.,]+)(.*?)$", line)
                    if match:
                        # Jika menemukan entri baru, simpan entri sebelumnya dulu
                        if current_entry:
                            extracted_data.append(current_entry)
                        # Mulai entri baru
                        no_urut = match.group(1)
                        nama_barang = f"Rp {match.group(2)}{match.group(3)}"
                        current_entry = [no_urut, nama_barang]
                    else:
                        # Jika tidak cocok dengan pola utama, kemungkinan lanjutan dari baris sebelumnya
                        if current_entry:
                            current_entry[1] += f" {line}"

    # Tambahkan entri terakhir jika ada
    if current_entry:
        extracted_data.append(current_entry)
    
    return extracted_data

def generate_download_link(df):
    output = BytesIO()
    df.to_csv(output, index=False, encoding="utf-8-sig")  # Kompatibel dengan Excel
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
