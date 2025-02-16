import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
from datetime import datetime

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF dan mengonversinya ke format tabel.
    """
    data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                try:
                  # Menangkap informasi faktur
                    no_fp = re.search(r'INVOICE #\s*(\d+)', text)
                    nama_penjual = re.search(r'PT\.\s*([A-Z\s]+)', text)
                    nama_pembeli = re.search(r'TO CUSTOMER\s*([A-Z\s]+)', text)
                    barang = re.search(r'Note\s*(.*?)\s*INVOICE', text, re.DOTALL)
                    harga_qty_match = re.search(r'@Rp\.\s*([\d,.]+)', text)
                    qty_match = re.search(r'Sewa\s*(\d+)\s*user', text)
                    tanggal_faktur = re.search(r'DATE\s*(\d{2}/\d{2}/\d{4})', text)
                    dpp_match = re.search(r'Subtotal\s*([\d,.]+)IDR', text)
                    ppn_match = re.search(r'VAT 11%\s*([\d,.]+)IDR', text)
                    
                    # Parsing data
                    no_fp = f"040025{no_fp.group(1)}" if no_fp else ""
                    nama_penjual = "PT. " + nama_penjual.group(1).strip() if nama_penjual else ""
                    nama_pembeli = nama_pembeli.group(1).strip() if nama_pembeli else ""
                    barang = barang.group(1).strip().replace('\n', ' ') if barang else ""
                    harga = int(harga_qty_match.group(1).replace(',', '').replace('.', '')) if harga_qty_match else 0
                    qty = int(qty_match.group(1)) if qty_match else 1
                    total = harga * qty
                    unit = "Bulan"
                    dpp = int(dpp_match.group(1).replace(',', '').replace('.', '')) if dpp_match else 0
                    ppn = int(ppn_match.group(1).replace(',', '').replace('.', '')) if ppn_match else 0
                    tanggal_faktur = tanggal_faktur.group(1) if tanggal_faktur else ""
                    
                    if barang:
                        data.append([no_fp, nama_penjual, nama_pembeli, barang, harga, unit, qty, total, dpp, ppn, tanggal_faktur])
                except Exception as e:
                    st.error(f"Terjadi kesalahan dalam membaca halaman: {e}")
    return data


# Streamlit UI
st.title("Konversi Faktur Pajak PDF ke Excel")

uploaded_files = st.file_uploader("Upload Faktur Pajak (PDF, bisa lebih dari satu)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    
    for uploaded_file in uploaded_files:
        extracted_data = extract_data_from_pdf(uploaded_file)
        if extracted_data:
            all_data.extend(extracted_data)
    
    if all_data:
        df = pd.DataFrame(all_data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Barang", "Harga", "Unit", "QTY", "Total", "DPP", "PPN", "Tanggal Faktur"])
        
        # Hilangkan baris kosong dan reset index
        df = df[df['Barang'] != ""].reset_index(drop=True)
        df.index = df.index + 1  # Mulai index dari 1
        
        # Menampilkan pratinjau data
        st.write("### Pratinjau Data yang Diekstrak")
        st.dataframe(df)
        
        # Simpan ke Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=True, sheet_name='Faktur Pajak')
            writer.close()
        output.seek(0)
        
        st.download_button(label="📥 Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
