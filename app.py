import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
from io import BytesIO

# Fungsi untuk ekstrak data dari PDF
def extract_invoice_data(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    invoice_data = []
    pattern = re.compile(r"(\d+)\s+600600\s+([\w\s,.-]+)SJ: ([\w\d]+), Tanggal:\s+(\d{2}/\d{2}/\d{4})\s+Rp ([\d,.]+) x ([\d,.]+) Kilogram\s+Potongan Harga = Rp ([\d,.]+)\s+PPnBM \(0,00%\) = Rp ([\d,.]+)\s+([\d,.]+)")
    
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

# Streamlit UI
st.title("Ekstraksi Data Faktur Pajak dari PDF")
st.write("Unggah file PDF untuk mengekstrak detail transaksi.")

uploaded_file = st.file_uploader("Pilih file PDF", type="pdf")

if uploaded_file is not None:
    st.success("File berhasil diunggah!")
    
    # Ekstrak data
    df = extract_invoice_data(uploaded_file)

    # Tampilkan hasil dalam tabel
    st.dataframe(df)

    # Tambahkan opsi untuk mengunduh sebagai Excel
    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    st.download_button(label="Unduh sebagai Excel",
                       data=output,
                       file_name="Hasil_Ekstraksi.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
