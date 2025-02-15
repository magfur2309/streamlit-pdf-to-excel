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
                
                try:
                    # Parsing data dari teks
                    no_fp = lines[3].split(':')[-1].strip() if len(lines) > 3 else ""
                    nama_penjual = lines[5].split(':')[-1].strip() if len(lines) > 5 else ""
                    nama_pembeli = lines[10].split(':')[-1].strip() if len(lines) > 10 else ""
                    barang = lines[17].strip() if len(lines) > 17 else ""

                    try:
                        harga = int(lines[18].split('x')[0].replace('Rp ', '').replace(',', '')) if len(lines) > 18 else 0
                    except ValueError:
                        harga = 0
                    
                    unit = "Bulan"

                    try:
                        qty = int(lines[18].split('x')[-1].split('Bulan')[0].strip()) if len(lines) > 18 else 0
                    except ValueError:
                        qty = 0
                    
                    total = harga * qty

                    try:
                        dpp = int(lines[22].split()[-1].replace(',', '')) if len(lines) > 22 else 0
                    except ValueError:
                        dpp = 0

                    try:
                        ppn = int(lines[24].split()[-1].replace(',', '')) if len(lines) > 24 else 0
                    except ValueError:
                        ppn = 0

                    tanggal_faktur = lines[-4].split(',')[-1].strip() if len(lines) > 4 else ""

                    data.append([no_fp, nama_penjual, nama_pembeli, barang, harga, unit, qty, total, dpp, ppn, tanggal_faktur])
                
                except Exception as e:
                    print(f"Terjadi kesalahan dalam membaca halaman: {e}")

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
