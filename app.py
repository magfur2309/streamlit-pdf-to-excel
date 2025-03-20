import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re

def extract_invoice_data(pdf_path):
    doc = fitz.open(pdf_path)
    invoice_data = []
    
    pattern = re.compile(r"(\\d+)\\s+600600\\s+([\\w\\s,.-]+)SJ: ([\\w\\d]+), Tanggal:\\s+(\\d{2}/\\d{2}/\\d{4})\\s+Rp ([\\d,.]+) x ([\\d,.]+) Kilogram\\s+Potongan Harga = Rp ([\\d,.]+)\\s+PPnBM \\(0,00%\\) = Rp ([\\d,.]+)\\s+([\\d,.]+)")
    
    for page in doc:
        text = page.get_text("text")
        matches = pattern.findall(text)
        
        for match in matches:
            invoice_data.append({
                "No": int(match[0]),
                "Kode Barang": "600600",
                "Nama Barang": match[1].strip(),
                "SJ": match[2],
                "Tanggal": match[3],
                "Harga per Kg (Rp)": match[4],
                "Jumlah (Kg)": match[5],
                "Potongan Harga (Rp)": match[6],
                "PPnBM (Rp)": match[7],
                "Total Harga (Rp)": match[8]
            })
    
    return pd.DataFrame(invoice_data)

st.title("Ekstraksi Data Faktur Pajak dari PDF")
uploaded_file = st.file_uploader("Upload file PDF", type="pdf")

if uploaded_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    df_result = extract_invoice_data("temp.pdf")
    st.write(df_result)

    # Tombol untuk download hasil sebagai Excel
    st.download_button(
        label="Download Excel",
        data=df_result.to_csv(index=False),
        file_name="Hasil_Ekstraksi.csv",
        mime="text/csv"
    )
