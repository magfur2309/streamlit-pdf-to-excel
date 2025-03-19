import streamlit as st
import pdfplumber
import pandas as pd

def extract_data_from_pdf(pdf_file):
    extracted_data = []
    missing_numbers = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Pastikan baris memiliki cukup kolom dan elemen pertama mengandung angka atau kosong (untuk menangkap semua baris)
                    if row and len(row) >= 3:
                        nomor = row[0].strip() if row[0] and any(c.isdigit() for c in row[0]) else None
                        nama_barang = row[1].strip() if row[1] else ""
                        harga_jual = row[-1].replace("Rp", "").replace(",", "").strip() if row[-1] else "0"
                        
                        try:
                            harga_jual = float(harga_jual)
                        except ValueError:
                            harga_jual = None
                        
                        extracted_data.append([nomor, nama_barang, harga_jual])
    
    # Konversi data ke DataFrame
    df = pd.DataFrame(extracted_data, columns=["No.", "Nama Barang Kena Pajak / Jasa Kena Pajak", "Harga Jual (Rp)"])
    
    # Ubah kolom No. menjadi angka, kosong diisi NaN
    df["No."] = pd.to_numeric(df["No."], errors='coerce')
    
    # Cek jika ada nomor yang hilang dalam urutan
    all_numbers = set(range(int(df["No."].min()), int(df["No."].max()) + 1))
    extracted_numbers = set(df["No."].dropna().astype(int))
    missing_numbers = sorted(all_numbers - extracted_numbers)
    
    # Debugging: Tampilkan nomor yang hilang
    if missing_numbers:
        st.write(f"Nomor yang hilang dalam hasil ekstraksi: {missing_numbers}")
    
    # Isi nomor yang kosong dengan interpolasi atau metode yang lebih akurat
    df["No."].fillna(method='ffill', inplace=True)  # Isi nomor yang kosong dengan nomor sebelumnya
    df = df.sort_values(by=["No."], na_position='last').reset_index(drop=True)  # Pastikan urutan nomor benar
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
