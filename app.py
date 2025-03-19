import streamlit as st
import pdfplumber
import pandas as pd

def extract_data_from_pdf(pdf_file):
    extracted_data = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()  # Menggunakan extract_tables untuk menangkap semua tabel
            for table in tables:
                for row in table:
                    # Periksa apakah baris memiliki cukup kolom dan elemen pertama adalah angka (nomor urut)
                    if row and len(row) >= 3 and row[0] and row[0].strip().isdigit():
                        nomor = int(row[0].strip())
                        nama_barang = row[1].strip() if row[1] else ""
                        harga_jual = row[-1].replace("Rp", "").replace(",", "").strip() if row[-1] else "0"
                        
                        try:
                            harga_jual = float(harga_jual)
                        except ValueError:
                            harga_jual = None
                        
                        extracted_data.append([nomor, nama_barang, harga_jual])
    
    # Pastikan semua nomor urut terbaca
    df = pd.DataFrame(extracted_data, columns=["No.", "Nama Barang Kena Pajak / Jasa Kena Pajak", "Harga Jual (Rp)"])
    df = df.sort_values(by=["No."]).reset_index(drop=True)  # Pastikan urutan nomor benar
    return df

def main():
    st.title("Ekstraksi Data dari PDF Faktur Pajak")
    
    uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])
    
    if uploaded_file is not None:
        df_extracted = extract_data_from_pdf(uploaded_file)
        
        st.write("### Hasil Ekstraksi")
        st.dataframe(df_extracted)
        
        if not df_extracted.empty:
            excel_file = "extracted_invoice_data.xlsx"
            df_extracted.to_excel(excel_file, index=False)
            
            with open(excel_file, "rb") as f:
                st.download_button("Unduh Hasil dalam Excel", f, file_name=excel_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()
