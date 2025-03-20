import streamlit as st
import pdfplumber
import pandas as pd
import re

def extract_transactions(pdf_path):
    transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split("\n")
                for line in lines:
                    match = re.match(r"(\d+)\s+(\d+)\s+([A-Z0-9 ,.-]+)\s+Rp ([\d.,]+) x ([\d.,]+) Kilogram\s+Rp ([\d.,]+)", line)
                    if match:
                        transactions.append({
                            "No": match.group(1),
                            "Kode Barang": match.group(2),
                            "Nama Barang": match.group(3).strip(),
                            "Harga per Kg (Rp)": match.group(4),
                            "Jumlah (Kg)": match.group(5),
                            "Total Harga (Rp)": match.group(6),
                        })
    
    return pd.DataFrame(transactions)

def main():
    st.title("Ekstrak Detail Transaksi dari PDF")
    uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])
    
    if uploaded_file is not None:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.read())
        
        df = extract_transactions("temp.pdf")
        
        if not df.empty:
            st.write("### Data Transaksi")
            st.dataframe(df)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Unduh CSV", data=csv, file_name="transaksi.csv", mime="text/csv")
        else:
            st.error("Tidak ditemukan data transaksi dalam PDF.")

if __name__ == "__main__":
    main()
