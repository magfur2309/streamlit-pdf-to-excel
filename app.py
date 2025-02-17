import pandas as pd
import re
import streamlit as st

try:
    import pdfplumber
except ModuleNotFoundError:
    st.error("Module 'pdfplumber' tidak ditemukan. Silakan install dengan 'pip install pdfplumber'.")
    pdfplumber = None

def extract_table_from_pdf(pdf_file):
    if pdfplumber is None:
        return None
    
    extracted_data = []
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_table()
                if tables:
                    for row in tables:
                        if row and not any("Uang Muka / Termin Jasa (Rp)" in str(cell) for cell in row):
                            extracted_data.append(row)
    except Exception as e:
        st.error(f"Error saat membaca PDF: {e}")
        return None
    
    return extracted_data if extracted_data else None

def process_pdf(pdf_file):
    data = extract_table_from_pdf(pdf_file)
    if data is None:
        st.error("Gagal mengekstrak data Barang. Pastikan format faktur sesuai.")
        return None
    
    df = pd.DataFrame(data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Barang", "Harga", "Unit", "QTY", "Total", "DPP", "PPN", "Tanggal Faktur"])
    return df

def main():
    st.title("Ekstrak PDF ke Excel")
    uploaded_file = st.file_uploader("Upload file PDF", type=["pdf"])
    
    if uploaded_file is not None:
        df = process_pdf(uploaded_file)
        if df is not None:
            st.write("### Data Barang:")
            st.dataframe(df)
            
            # Simpan ke Excel
            excel_file = "output.xlsx"
            df.to_excel(excel_file, index=False)
            with open(excel_file, "rb") as file:
                st.download_button("Download Excel", file, file_name="data_barang.xlsx")
        else:
            st.error("Ekstraksi gagal. Coba lagi dengan format PDF yang sesuai.")

if __name__ == "__main__":
    main()
