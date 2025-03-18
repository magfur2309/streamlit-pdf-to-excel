import streamlit as st
import pandas as pd
import pdfplumber
import re

def extract_filtered_data(pdf_file):
    extracted_data = []
    
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

        lines = full_text.split("\n")
        nomor_urut = 1  # Inisialisasi nomor urut
        for i in range(len(lines)):
            match = re.match(r"(\d+)\s+(\d+)\s+Rp ([\d,.]+) x ([\d,.]+) Kilogram\s+([\d,.]+)", lines[i])
            if match and i+3 < len(lines):
                potongan_harga = re.search(r"Potongan Harga = Rp ([\d,.]+)", lines[i+1])
                ppnbm = re.search(r"PPnBM \([\d,.]+%\) = Rp ([\d,.]+)", lines[i+2])
                nama_barang = lines[i+3]

                extracted_data.append({
                    "Nomor": nomor_urut,  # Gunakan nomor urut otomatis
                    "Kode": match.group(2),
                    "Harga per Kg": match.group(3),
                    "Berat (Kg)": match.group(4),
                    "Total Harga": match.group(5),
                    "Potongan Harga": potongan_harga.group(1) if potongan_harga else "0",
                    "PPnBM": ppnbm.group(1) if ppnbm else "0",
                    "Nama Barang": nama_barang
                })
                nomor_urut += 1  # Tambah nomor urut agar tidak terlewat
    
    return pd.DataFrame(extracted_data)

def main():
    st.title("Ekstrak Data PDF ke Excel")
    uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])
    
    if uploaded_file:
        st.success("File berhasil diunggah!")
        df = extract_filtered_data(uploaded_file)
        
        if not df.empty:
            st.write("### Data yang Diekstrak")
            st.table(df)
            
            output_file = "filtered_data.xlsx"
            df.to_excel(output_file, index=False)
            st.download_button("Unduh Excel", data=open(output_file, "rb"), file_name="data_ekstrak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("Data tidak ditemukan atau format tidak sesuai.")

if __name__ == "__main__":
    main()
