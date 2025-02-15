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
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                st.warning(f"Halaman {page_num + 1} tidak memiliki teks. Jika PDF berupa gambar, gunakan OCR.")
                continue  # Lewati halaman kosong atau gambar
            
            lines = text.split('\n')
            
            def find_value(key):
                for line in lines:
                    if key.lower() in line.lower():
                        parts = line.split(':')
                        if len(parts) > 1:
                            return parts[-1].strip()
                return None
            
            no_fp = find_value("Faktur Pajak") or find_value("Nomor Faktur")
            nama_penjual = find_value("Nama Penjual")
            nama_pembeli = find_value("Nama Pembeli")
            barang = find_value("Deskripsi Barang") or find_value("Nama Barang")
            tanggal_faktur = find_value("Tanggal Faktur") or find_value("Tanggal")

            harga, qty, total, dpp, ppn = None, None, None, None, None
            unit = "Unit"
            
            for line in lines:
                if 'Rp' in line and 'x' in line:
                    try:
                        parts = line.replace('Rp', '').replace(',', '').split('x')
                        harga = int(parts[0].strip())
                        qty = int(parts[1].split()[0].strip())
                        total = harga * qty
                        unit = "Bulan" if "Bulan" in line else "Unit"
                    except Exception:
                        harga, qty, total = None, None, None
                        
                if "Dasar Pengenaan Pajak" in line:
                    try:
                        dpp = int(line.split()[-1].replace(',', ''))
                    except Exception:
                        dpp = None
                
                if "PPN" in line:
                    try:
                        ppn = int(line.split()[-1].replace(',', ''))
                    except Exception:
                        ppn = None
            
            # Debugging: Tampilkan hasil sementara
            st.text(f"Extracted from page {page_num + 1}: {no_fp}, {nama_penjual}, {nama_pembeli}, {barang}, {harga}, {unit}, {qty}, {total}, {dpp}, {ppn}, {tanggal_faktur}")

            if no_fp and nama_penjual and nama_pembeli:
                data.append([no_fp, nama_penjual, nama_pembeli, barang, harga, unit, qty, total, dpp, ppn, tanggal_faktur])
    
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
        st.error("Gagal mengekstrak data. Pastikan format faktur sesuai atau gunakan OCR jika PDF berbentuk gambar.")
