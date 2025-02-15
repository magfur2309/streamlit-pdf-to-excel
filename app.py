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
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                text = page.extract_text()
                
                if not text and not table:
                    continue  # Lewati halaman kosong
                
                def find_value(key, text):
                    match = re.search(fr'{key}\s*:?\s*(.*)', text, re.IGNORECASE)
                    return match.group(1).strip() if match else None
                
                no_fp = find_value("Faktur Pajak", text)
                nama_penjual = find_value("Nama Penjual", text)
                nama_pembeli = find_value("Nama Pembeli", text)
                barang = find_value("Deskripsi Barang", text)
                tanggal_faktur = find_value("Tanggal Faktur", text)
                
                harga, qty, total, dpp, ppn = None, None, None, None, None
                unit = "Unit"
                
                if table:
                    for row in table:
                        row_text = ' '.join([cell if cell else '' for cell in row])
                        if 'Rp' in row_text and 'x' in row_text:
                            try:
                                parts = re.findall(r'\d+', row_text.replace('Rp', '').replace(',', ''))
                                if len(parts) >= 2:
                                    harga = int(parts[0])
                                    qty = int(parts[1])
                                    total = harga * qty
                                    unit = "Bulan" if "Bulan" in row_text else "Unit"
                            except Exception:
                                harga, qty, total = None, None, None
                        
                        if "Dasar Pengenaan Pajak" in row_text:
                            try:
                                dpp = int(re.findall(r'\d+', row_text.replace(',', ''))[-1])
                            except Exception:
                                dpp = None
                    
                        if "PPN" in row_text:
                            try:
                                ppn = int(re.findall(r'\d+', row_text.replace(',', ''))[-1])
                            except Exception:
                                ppn = None
                
                if no_fp and nama_penjual and nama_pembeli:
                    data.append([no_fp, nama_penjual, nama_pembeli, barang, harga, unit, qty, total, dpp, ppn, tanggal_faktur])
    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca PDF: {e}")
        return None
    
    return data if data else None

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
        st.error("Gagal mengekstrak data. Pastikan format faktur sesuai atau coba gunakan OCR jika PDF berbentuk gambar.")
