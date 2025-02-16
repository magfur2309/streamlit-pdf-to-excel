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
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                try:
                    # Menggunakan regex untuk menangkap data dengan lebih fleksibel
                    no_fp = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', text)
                    nama_penjual = re.search(r'Pengusaha Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                    nama_pembeli = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                    barang = re.search(r'Nama Barang Kena Pajak / Jasa Kena Pajak\s*(.+)', text)
                    harga_qty_match = re.search(r'Rp ([\d,.]+) x ([\d,.]+) Bulan', text)
                    dpp = re.search(r'Dasar Pengenaan Pajak\s*([\d,.]+)', text)
                    ppn = re.search(r'Jumlah PPN \(Pajak Pertambahan Nilai\)\s*([\d,.]+)', text)
                    tanggal_faktur = re.search(r'KOTA .+, (\d+ \w+ \d{4})', text)

                    no_fp = no_fp.group(1) if no_fp else ""
                    nama_penjual = nama_penjual.group(1).strip() if nama_penjual else ""
                    nama_pembeli = nama_pembeli.group(1).strip() if nama_pembeli else ""
                    barang = barang.group(1).strip() if barang else ""
                    harga = int(harga_qty_match.group(1).replace(',', '')) if harga_qty_match else 0
                    qty = int(harga_qty_match.group(2).replace(',', '')) if harga_qty_match else 0
                    unit = "Bulan"
                    total = harga * qty
                    dpp = int(dpp.group(1).replace(',', '')) if dpp else 0
                    ppn = int(ppn.group(1).replace(',', '')) if ppn else 0
                    tanggal_faktur = tanggal_faktur.group(1) if tanggal_faktur else ""

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
        
        # Menampilkan pratinjau data
        st.write("### Pratinjau Data yang Diekstrak")
        st.dataframe(df)
        
        # Simpan ke Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Faktur Pajak')
            writer.close()
        output.seek(0)
        
        st.download_button(label="📥 Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
