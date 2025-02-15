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
                
                # Debugging mode (opsional)
                # st.text("\n".join(lines))
                
                no_fp = next((line.split(':')[-1].strip() for line in lines if "Faktur Pajak" in line), None)
                nama_penjual = next((line.split(':')[-1].strip() for line in lines if "Nama Penjual" in line), None)
                nama_pembeli = next((line.split(':')[-1].strip() for line in lines if "Nama Pembeli" in line), None)
                barang = next((line.strip() for line in lines if "Deskripsi Barang" in line), None)
                
                harga_line = next((line for line in lines if 'Rp' in line and 'x' in line), None)
                if harga_line:
                    try:
                        harga = int(harga_line.split('x')[0].replace('Rp ', '').replace(',', ''))
                        qty = int(harga_line.split('x')[-1].split('Bulan')[0].strip())
                    except ValueError:
                        harga, qty = None, None
                else:
                    harga, qty = None, None
                
                unit = "Bulan" if qty else "Unit"
                total = harga * qty if harga and qty else None
                dpp = next((int(line.split()[-1].replace(',', '')) for line in lines if "Dasar Pengenaan Pajak" in line), None)
                ppn = next((int(line.split()[-1].replace(',', '')) for line in lines if "PPN" in line), None)
                tanggal_faktur = next((line.split(',')[-1].strip() for line in lines if "Tanggal Faktur" in line), None)
                
                if no_fp and nama_penjual and nama_pembeli:
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
