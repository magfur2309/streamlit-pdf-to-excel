import streamlit as st
import camelot
import pandas as pd
import os

# Fungsi untuk ekstrak tabel dari PDF menggunakan Camelot
def extract_data_from_pdf(pdf_path):
    try:
        # Ekstrak semua tabel dari seluruh halaman
        tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")

        # Jika tidak ada tabel yang ditemukan
        if tables.n == 0:
            st.error("Tidak ada tabel yang terdeteksi dalam PDF. Pastikan PDF berisi tabel berbasis teks.")
            return pd.DataFrame()

        # Gabungkan semua tabel yang ditemukan
        df_list = [table.df for table in tables]
        df_combined = pd.concat(df_list, ignore_index=True)

        # Menghapus baris header tambahan jika ada
        df_combined.columns = df_combined.iloc[0]  # Jadikan baris pertama sebagai header
        df_combined = df_combined[1:].reset_index(drop=True)  # Hapus baris pertama

        # Normalisasi nama kolom
        df_combined.columns = ["No.", "Nama Barang", "Harga Jual (Rp)"]

        # Membersihkan data
        df_combined["No."] = pd.to_numeric(df_combined["No."], errors='coerce')
        df_combined["Harga Jual (Rp)"] = df_combined["Harga Jual (Rp)"].str.replace("Rp", "").str.replace(",", "").str.strip()
        df_combined["Harga Jual (Rp)"] = pd.to_numeric(df_combined["Harga Jual (Rp)"], errors='coerce')

        # Mengisi nomor yang kosong karena halaman terpisah
        df_combined["No."].fillna(method="ffill", inplace=True)

        return df_combined

    except Exception as e:
        st.error(f"Terjadi kesalahan saat mengekstrak data: {e}")
        return pd.DataFrame()

# Streamlit UI
def main():
    st.title("Ekstraksi Data dari PDF Faktur Pajak")
    
    # Upload file PDF
    uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])
    
    if uploaded_file is not None:
        # Simpan file sementara
        pdf_path = "temp_uploaded.pdf"
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Ekstraksi data
        df_extracted = extract_data_from_pdf(pdf_path)

        # Menampilkan hasil ekstraksi
        if not df_extracted.empty:
            st.write("### Hasil Ekstraksi Data:")
            st.dataframe(df_extracted)

            # Simpan sebagai file Excel
            excel_path = "extracted_data.xlsx"
            df_extracted.to_excel(excel_path, index=False)

            # Unduh file Excel
            with open(excel_path, "rb") as f:
                st.download_button("Unduh Hasil dalam Excel", f, file_name="extracted_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        # Hapus file sementara
        os.remove(pdf_path)

if __name__ == "__main__":
    main()
