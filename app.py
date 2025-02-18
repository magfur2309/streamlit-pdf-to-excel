import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

def extract_invoice_data(pdf_file):
    data = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')
            
            invoice_number = ""
            seller_name = ""
            buyer_name = ""
            current_item = ""
            
            for line in lines:
                # Mendeteksi nomor faktur pajak
                match_fp = re.search(r'\b(\d{16})\b', line)
                if match_fp:
                    invoice_number = match_fp.group(1)
                    continue
                
                # Mendeteksi nama penjual dan pembeli
                if "SOFIE FASHION IND" in line:
                    seller_name = "SOFIE FASHION IND"
                if "CASH" in line:
                    buyer_name = "CASH"
                
                # Mendeteksi baris yang berisi barang dan harga
                match_item = re.search(r'([A-Za-z\-\s]+)\s+Rp ([\d.,]+) x ([\d.,]+) (\w+)', line)
                
                if match_item:
                    # Jika ada barang baru, simpan barang sebelumnya
                    if current_item:
                        data.append([invoice_number, seller_name, buyer_name, current_item])
                    
                    current_item = match_item.group(1).strip()
                else:
                    # Jika baris ini tidak cocok dengan harga, maka ini adalah lanjutan dari nama barang
                    if re.search(r'\d+', line) is None:
                        current_item += " " + line.strip()
            
            # Simpan item terakhir
            if current_item:
                data.append([invoice_number, seller_name, buyer_name, current_item])
    
    return data

st.title("Ekstraksi Faktur Pajak dari PDF")

uploaded_file = st.file_uploader("Upload file PDF", type=["pdf"])

if uploaded_file is not None:
    extracted_data = extract_invoice_data(uploaded_file)
    
    df = pd.DataFrame(extracted_data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Barang"])
    st.write("### Pratinjau Data yang Diekstrak")
    st.dataframe(df)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Faktur')
    
    st.download_button(
        label="Download Excel",
        data=output.getvalue(),
        file_name="faktur_pajak.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
