import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

def extract_data_from_pdf(pdf_file):
    data = []
    last_no_urut = None
    current_nama_barang = ""
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table:
                    if len(row) >= 4 and row[0].isdigit():
                        last_no_urut = row[0]
                        current_nama_barang = row[2].replace("\n", " ").strip()
                        
                        harga_qty_info = re.search(r'Rp\s*([\d.,]+)\s*x\s*([\d.,]+)\s*(\w+)', row[2])
                        if harga_qty_info:
                            harga = float(harga_qty_info.group(1).replace('.', '').replace(',', '.'))
                            qty = float(harga_qty_info.group(2).replace('.', '').replace(',', '.'))
                            unit = harga_qty_info.group(3)
                        else:
                            harga, qty, unit = 0, 0, "Unknown"
                        
                        total = harga * qty
                        dpp = total / 1.11
                        ppn = total - dpp
                        
                        data.append([last_no_urut, current_nama_barang, harga, unit, qty, total, dpp, ppn])
                    
                    elif last_no_urut and row[2].strip():
                        current_nama_barang += " " + row[2].replace("\n", " ").strip()
                        data[-1][1] = current_nama_barang
    
    return data

st.title("Ekstraksi Faktur Pajak ke Excel")
uploaded_files = st.file_uploader("Upload file PDF", accept_multiple_files=True, type=["pdf"])

data_ekstraksi = []
if uploaded_files:
    for uploaded_file in uploaded_files:
        extracted_data = extract_data_from_pdf(uploaded_file)
        data_ekstraksi.extend(extracted_data)
    
    df = pd.DataFrame(data_ekstraksi, columns=["No Urut", "Nama Barang", "Harga", "Unit", "Quantity", "Total", "DPP", "PPN"])
    st.dataframe(df)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Faktur Pajak')
    st.download_button("Download Excel", data=output.getvalue(), file_name="faktur_pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
