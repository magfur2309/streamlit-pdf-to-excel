import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
from io import BytesIO

def extract_text_from_pdf(uploaded_file):
    """Ekstrak teks dari PDF menggunakan PyMuPDF."""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
    return text


def parse_invoice_data(text):
    """Parsing data transaksi dari teks faktur pajak."""
    lines = text.split("\n")
    transaksi = []
    
    for i, line in enumerate(lines):
        parts = line.split()
        if len(parts) > 5 and parts[0].isdigit():
            try:
                no = int(parts[0])
                kode_barang = parts[1]
                nama_barang = " ".join(parts[2:-4])
                berat = float(parts[-4].replace(",", ""))
                harga_kg = float(parts[-3].replace(",", ""))
                total_harga = float(parts[-1].replace(",", ""))
                transaksi.append((no, kode_barang, nama_barang, berat, harga_kg, total_harga))
            except ValueError:
                continue
    
    return pd.DataFrame(transaksi, columns=["No", "Kode Barang", "Nama Barang", "Berat (Kg)", "Harga per Kg (Rp)", "Total Harga (Rp)"])

def main():
    st.title("Ekstraksi Data Faktur Pajak dari PDF")
    
    uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])
    
if uploaded_file is not None:
    try:
        text = extract_text_from_pdf(uploaded_file)
        df = parse_invoice_data(text)
        st.dataframe(df)
    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca PDF: {str(e)}")
else:
    st.warning("Silakan unggah file PDF terlebih dahulu.")

            
            if not df.empty:
                st.success("Ekstraksi berhasil!")
                st.dataframe(df)
                
                # Konversi DataFrame ke file Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Data Transaksi')
                output.seek(0)
                
                st.download_button(
                    label="📥 Unduh Data dalam Excel",
                    data=output,
                    file_name="Faktur_Transaksi.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("Gagal mengekstrak data dari PDF. Periksa format file.")

if __name__ == "__main__":
    main()
