import pandas as pd
import re
import streamlit as st

try:
    import pdfplumber
except ModuleNotFoundError:
    st.error("Module 'pdfplumber' tidak ditemukan. Silakan install dengan 'pip install pdfplumber'.")
    pdfplumber = None

def extract_text_from_pdf(pdf_file):
    if pdfplumber is None:
        return None
    
    extracted_text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() + "\n"
    except Exception as e:
        st.error(f"Error saat membaca PDF: {e}")
        return None
    return extracted_text

def clean_barang_data(text):
    if not text:
        return []
    
    lines = text.split("\n")
    start_index = next((i for i, line in enumerate(lines) if "Barang" in line), None)
    
    if start_index is None or start_index + 1 >= len(lines):
        st.warning("Tidak ada data barang yang ditemukan.")
        return []
    
    barang_list = []
    for line in lines[start_index + 1:]:
        if "Uang Muka / Termin Jasa (Rp)" in line:
            continue  # Lewati baris yang mengandung informasi ini
        barang_info = re.split(r'\s{2,}', line)  # Pisahkan berdasarkan spasi panjang
        if len(barang_info) >= 9:  # Pastikan data memiliki jumlah kolom yang sesuai
            barang_list.append(barang_info)
    
    return barang_list if barang_list else []

def process_pdf(pdf_file):
    text = extract_text_from_pdf(pdf_file)
    if text is None:
        return None
    
    barang_data = clean_barang_data(text)
    
    if not barang_data:
        st.error("Gagal mengekstrak data Barang. Pastikan format faktur sesuai.")
        return None
    
    df = pd.DataFrame(barang_data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Barang", "Harga", "Unit", "QTY", "Total", "DPP", "PPN", "Tanggal Faktur"])
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
