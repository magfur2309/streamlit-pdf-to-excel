import streamlit as st
import pandas as pd
import pdfplumber
import re

def extract_data_from_pdf(pdf_file):
    extracted_data = []
    
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        
        st.text_area("Teks Mentah dari PDF", full_text, height=300)
        
        lines = full_text.split("\n")
        for line in lines:
            match = re.match(r"(\d+)\s+(\d+)\s+([A-Z0-9,\s]+),\s+SJ:\s+([A-Z0-9]+),\s+Tanggal:\s+(\d{2}/\d{2}/\d{4})\s+Rp ([\d,.]+) x ([\d,.]+) Kilogram.*Rp ([\d,.]+)", line)
            if match:
                extracted_data.append({
                    "Nomor": match.group(1),
                    "Kode": match.group(2),
                    "Nama Barang": match.group(3),
                    "SJ": match.group(4),
                    "Tanggal": match.group(5),
                    "Harga per Kg": match.group(6),
                    "Berat (Kg)": match.group(7),
                    "Total Harga": match.group(8)
                })
    
    return pd.DataFrame(extracted_data)

def main():
    st.title("Ekstrak Data PDF ke Excel")
    uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])
    
    if uploaded_file:
        st.success("File berhasil diunggah!")
        df = extract_data_from_pdf(uploaded_file)
        
        if not df.empty:
            st.write("### Data yang Diekstrak")
            st.dataframe(df)
            
            output_file = "extracted_data.xlsx"
            df.to_excel(output_file, index=False)
            st.download_button("Unduh Excel", data=open(output_file, "rb"), file_name="data_ekstrak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("Data tidak ditemukan atau format tidak sesuai.")

if __name__ == "__main__":
    main()
