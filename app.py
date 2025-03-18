import streamlit as st
import pandas as pd
import pdfplumber
import re

def extract_data_from_pdf(pdf_file):
    extracted_data = []
    
    with pdfplumber.open(pdf_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        
        lines = full_text.split("\n")
        
        pattern = re.compile(
            r"(\d+)\s+(\d+)\s+Rp ([\d,.]+) x ([\d,.]+) Kilogram ([\d,.]+)\n"
            r"Potongan Harga = Rp ([\d,.]+)\n"
            r"PPnBM \([\d,.]+%\) = Rp ([\d,.]+)\n"
            r"(.+?), SJ: (\S+), Tanggal:\s+(\d{2}/\d{2}/\d{4})"
        )

        for i in range(len(lines)):
            match = pattern.match("\n".join(lines[i:i+4]))  # Gabungkan 4 baris untuk mencocokkan pola
            if match:
                extracted_data.append({
                    "Nomor": int(match.group(1)),
                    "Kode": match.group(2),
                    "Harga per Kg": match.group(3),
                    "Berat (Kg)": match.group(4),
                    "Total Harga": match.group(5),
                    "Potongan Harga": match.group(6),
                    "PPnBM": match.group(7),
                    "Nama Barang": match.group(8),
                    "SJ": match.group(9),
                    "Tanggal": match.group(10)
                })
    
    df = pd.DataFrame(extracted_data)
    df = df.sort_values(by="Nomor").reset_index(drop=True)  # Pastikan nomor urut tidak terlewat
    return df

def main():
    st.title("Ekstrak Data PDF ke Excel")
    uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])
    
    if uploaded_file:
        st.success("File berhasil diunggah!")
        df = extract_data_from_pdf(uploaded_file)
        
        if not df.empty:
            st.write("### Data yang Diekstrak")
            st.dataframe(df)  # Tampilkan sebagai tabel interaktif
            
            # Simpan data ke file Excel
            output_file = "extracted_data.xlsx"
            df.to_excel(output_file, index=False)
            
            # Tombol unduh file Excel
            st.download_button("Unduh Excel", data=open(output_file, "rb"), 
                               file_name="data_ekstrak.xlsx", 
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("Data tidak ditemukan atau format tidak sesuai.")

if __name__ == "__main__":
    main()
