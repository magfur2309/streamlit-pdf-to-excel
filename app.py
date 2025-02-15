import streamlit as st
import pandas as pd
import pdfplumber
import io

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF dan mengonversinya ke format tabel.
    """
    data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                
                # Parsing data dari teks
                if "Faktur Pajak" in text:
                    no_fp = lines[3].split(':')[-1].strip()
                    nama_penjual = lines[5].split(':')[-1].strip()
                    nama_pembeli = lines[10].split(':')[-1].strip()
                    barang = lines[17].strip()
                    harga = int(lines[18].split('x')[0].replace('Rp ', '').replace(',', ''))
                    unit = "Bulan"
                    qty = int(lines[18].split('x')[-1].split('Bulan')[0].strip())
                    total = harga * qty
                    dpp = int(lines[22].split()[-1].replace(',', ''))
                    ppn = int(lines[24].split()[-1].replace(',', ''))
                    tanggal_faktur = lines[-4].split(',')[-1].strip()
                    
                    data.append([no_fp, nama_penjual, nama_pembeli, barang, harga, unit, qty, total, dpp, ppn, tanggal_faktur])
    
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
