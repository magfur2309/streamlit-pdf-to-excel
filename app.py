import pandas as pd
import pdfplumber
import io
from google.colab import files

# Fungsi untuk ekstrak data dari PDF
def extract_data_from_pdf(pdf_path):
    data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split("\n")
                
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

# Upload file PDF
uploaded = files.upload()

# Proses setiap file yang diunggah
all_data = []
for filename in uploaded.keys():
    extracted_data = extract_data_from_pdf(filename)
    if extracted_data:
        all_data.extend(extracted_data)

# Jika ada data, buat DataFrame dan simpan ke Excel
if all_data:
    df = pd.DataFrame(all_data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Barang", "Harga", "Unit", "QTY", "Total", "DPP", "PPN", "Tanggal Faktur"])
    print("Data yang berhasil diekstrak:")
    print(df)

    # Simpan ke file Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Faktur Pajak')
        writer.close()
    output.seek(0)

    # Simpan file ke Google Colab
    with open("Faktur_Pajak.xlsx", "wb") as f:
        f.write(output.getbuffer())

    # Download file
    files.download("Faktur_Pajak.xlsx")
else:
    print("Gagal mengekstrak data. Pastikan format faktur sesuai.")
