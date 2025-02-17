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
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            # Pastikan jumlah kolom sesuai dengan format yang diharapkan
                            if len(row) >= 10:  # Bisa lebih fleksibel jika ada tambahan kolom
                                extracted_data.append(row[:10])  # Ambil 10 kolom pertama jika lebih
    except Exception as e:
        st.error(f"Error saat membaca PDF: {e}")
        return None
    
    return extracted_data if extracted_data else None

def process_pdf(pdf_file):
    data = extract_table_from_pdf(pdf_file)
    if data is None:
        st.error("Gagal mengekstrak data Barang. Pastikan format faktur sesuai.")
        return None
    
    # Debugging: Tampilkan isi data sebelum dibuat DataFrame
    st.write("Data mentah dari PDF:", data)
    
    try:
        df = pd.DataFrame(data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Barang", "Harga", "Unit", "QTY", "Total", "DPP", "PPN", "Tanggal Faktur"])
    except ValueError as e:
        st.error(f"Kesalahan dalam pembuatan DataFrame: {e}")
        return None
    
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
