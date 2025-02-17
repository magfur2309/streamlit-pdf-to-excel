import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF dan mengonversinya ke format tabel.
    """
    data = []
    full_text = ""
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    try:
        # Menangkap informasi faktur
        no_fp = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', full_text)
        nama_penjual = re.search(r'Pengusaha Kena Pajak:\s*Nama\s*:\s*(.+)', full_text)
        nama_pembeli = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*(.+)', full_text)

        # Menangkap informasi barang
        barang_regex = re.findall(r'(\d{1,2})\s+000000\s+(.+?)\s+Rp ([\d.,]+) x ([\d.,]+) Piece', full_text)

        for match in barang_regex:
            nomor, barang, harga, qty = match

            harga = int(float(harga.replace('.', '').replace(',', '.')))
            qty = int(float(qty.replace('.', '').replace(',', '.')))
            total = harga * qty

            data.append([no_fp.group(1) if no_fp else "",
                         nama_penjual.group(1).strip() if nama_penjual else "",
                         nama_pembeli.group(1).strip() if nama_pembeli else "",
                         barang.strip(),
                         harga, "Piece", qty, total])
    except Exception as e:
        st.error(f"Terjadi kesalahan dalam membaca file: {e}")

    return data


# Streamlit UI
st.title("Ekstraksi Faktur Pajak PDF ke Excel")

uploaded_files = st.file_uploader("Upload Faktur Pajak (PDF, bisa lebih dari satu)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    
    for uploaded_file in uploaded_files:
        extracted_data = extract_data_from_pdf(uploaded_file)
        if extracted_data:
            all_data.extend(extracted_data)
    
    if all_data:
        df = pd.DataFrame(all_data, columns=["No Faktur", "Nama Penjual", "Nama Pembeli", "No Urut", "Barang", "Harga", "QTY", "Total"])
        df = df.sort_values(by=["No Faktur", "No Urut"]).reset_index(drop=True)
        # Hapus kolom No Urut (jika ada di posisi tertentu)
        df = df.drop(columns=["No Urut"], errors="ignore")
        
        st.write("### Pratinjau Data yang Diekstrak")
        st.dataframe(df)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Faktur Pajak')
            writer.close()
        output.seek(0)
        
        st.download_button(label="📥 Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
