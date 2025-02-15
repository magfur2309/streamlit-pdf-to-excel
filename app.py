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

                # Debugging: tampilkan teks hasil ekstraksi
                # st.write("\n".join(lines))

                # Ekstraksi data dengan validasi
                no_fp = next((line.split(':')[-1].strip() for line in lines if "Faktur Pajak" in line), None)
                nama_penjual = next((line.split(':')[-1].strip() for line in lines if "Nama Penjual" in line), None)
                nama_pembeli = next((line.split(':')[-1].strip() for line in lines if "Nama Pembeli" in line), None)
                barang = next((line.strip() for line in lines if "Deskripsi Barang" in line), None)

                harga, qty, total, dpp, ppn = None, None, None, None, None

                # Ekstraksi harga & qty dengan validasi
                harga_line = next((line for line in lines if 'Rp' in line and 'x' in line), None)
                if harga_line:
                    try:
                        harga = int(harga_line.split('x')[0].replace('Rp', '').replace(',', '').strip())
                        qty = int(harga_line.split('x')[-1].split('Bulan')[0].strip())
                        total = harga * qty  # Hitung total harga
                    except ValueError:
                        harga, qty, total = None, None, None  # Default jika gagal parsing
                
                unit = "Bulan" if qty else "Unit"

                # Ekstraksi DPP dengan pengecekan kesalahan
                try:
                    dpp_line = next((line for line in lines if "Dasar Pengenaan Pajak" in line), None)
                    if dpp_line:
                        dpp = int(dpp_line.split()[-1].replace(',', '').strip())
                except ValueError:
                    dpp = None

                # Ekstraksi PPN dengan pengecekan kesalahan
                try:
                    ppn_line = next((line for line in lines if "PPN" in line), None)
                    if ppn_line:
                        ppn = int(ppn_line.split()[-1].replace(',', '').strip())
                except ValueError:
                    ppn = None

                # Ekstraksi tanggal faktur
                tanggal_faktur = next((line.split(',')[-1].strip() for line in lines if "Tanggal Faktur" in line), None)

                # Simpan hanya jika ada data faktur yang valid
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
