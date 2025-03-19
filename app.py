import streamlit as st
import pdfplumber
import pandas as pd

def extract_table_from_pdf(pdf_file):
    extracted_data = []
    last_nomor = None  # Menyimpan nomor terakhir
    pending_entry = None  # Menyimpan data yang mungkin terpotong di halaman
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row and len(row) >= 3:
                        nomor = row[0].strip() if row[0] and any(c.isdigit() for c in row[0]) else None
                        nama_barang = row[1].strip() if row[1] else ""
                        harga_jual = row[-1].replace("Rp", "").replace(",", "").strip() if row[-1] else "0"
                        
                        try:
                            harga_jual = float(harga_jual)
                        except ValueError:
                            harga_jual = None
                        
                        # Jika data terpotong dari halaman sebelumnya, gabungkan
                        if pending_entry and nomor is None:
                            pending_entry[1] += " " + nama_barang
                            pending_entry[2] = harga_jual
                            extracted_data.append(pending_entry)
                            pending_entry = None
                            continue
                        
                        # Jika nomor kosong tetapi nama barang ada, lanjutkan dari nomor sebelumnya
                        if nomor is None and last_nomor is not None:
                            nomor = last_nomor
                        else:
                            last_nomor = nomor
                        
                        # Simpan data, jika nama barang kosong, simpan sementara
                        if not nama_barang.strip():
                            pending_entry = [nomor, nama_barang, harga_jual]
                        else:
                            extracted_data.append([nomor, nama_barang, harga_jual])
    
    # Konversi ke DataFrame
    df = pd.DataFrame(extracted_data, columns=["No.", "Nama Barang Kena Pajak / Jasa Kena Pajak", "Harga Jual (Rp)"])
    
    # Isi nomor yang kosong dengan interpolasi
    df["No."] = pd.to_numeric(df["No."], errors='coerce')
    df["No."].fillna(method='ffill', inplace=True)
    df = df.sort_values(by=["No."], na_position='last').reset_index(drop=True)
    
    return df

def main():
    st.title("Ekstraksi Data dari PDF Faktur Pajak")

    uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])
    
    if uploaded_file is not None:
        df_extracted = extract_table_from_pdf(uploaded_file)
        
        st.write("### Hasil Ekstraksi")
        st.dataframe(df_extracted)
        
        if not df_extracted.empty:
            excel_file = "extracted_invoice_data.xlsx"
            df_extracted.to_excel(excel_file, index=False)
            
            with open(excel_file, "rb") as f:
                st.download_button("Unduh Hasil dalam Excel", f, file_name=excel_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()
