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
                text = page.extract_text()
                if not text:
                    continue  # Lewati halaman kosong
                
                lines = text.split('\n')
                
                def find_value(key_pattern):
                    for line in lines:
                        match = re.search(key_pattern, line, re.IGNORECASE)
                        if match:
                            return match.group(1).strip()
                    return None
                
                no_fp = find_value(r"Faktur Pajak[\s:]*(.*)")
                nama_penjual = find_value(r"Nama Penjual[\s:]*(.*)")
                nama_pembeli = find_value(r"Nama Pembeli[\s:]*(.*)")
                barang = find_value(r"Deskripsi Barang[\s:]*(.*)")
                tanggal_faktur = find_value(r"Tanggal Faktur[\s:]*(.*)")
                
                harga, qty, total, dpp, ppn = None, None, None, None, None
                unit = "Unit"
                
                for line in lines:
                    harga_match = re.search(r"Rp[\s]*([\d,.]+)[\s]*x[\s]*(\d+)", line)
                    if harga_match:
                        try:
                            harga = int(harga_match.group(1).replace(',', ''))
                            qty = int(harga_match.group(2))
                            total = harga * qty
                            unit = "Bulan" if "Bulan" in line else "Unit"
                        except Exception:
                            harga, qty, total = None, None, None
                    
                    dpp_match = re.search(r"Dasar Pengenaan Pajak[\s]*([\d,.]+)", line)
                    if dpp_match:
                        try:
                            dpp = int(dpp_match.group(1).replace(',', ''))
                        except Exception:
                            dpp = None
                    
                    ppn_match = re.search(r"PPN[\s]*([\d,.]+)", line)
                    if ppn_match:
                        try:
                            ppn = int(ppn_match.group(1).replace(',', ''))
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
        st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
