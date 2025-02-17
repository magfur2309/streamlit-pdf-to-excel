import os
import pdfplumber
import pandas as pd

# Path file PDF yang diunggah
pdf_path = "/mnt/data/FP Balai Diklat Keuangan Balikpapan BPPK - 00006065303.pdf"

# Pastikan file PDF tersedia sebelum diproses
if not os.path.exists(pdf_path):
    raise FileNotFoundError(f"File tidak ditemukan: {pdf_path}")

data_extracted = []

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        if not tables:
            print(f"Tidak ada tabel yang ditemukan di halaman {page_num + 1}")
        for table in tables:
            for row in table:
                if len(row) > 1 and all(row):  # Pastikan tidak ada nilai kosong
                    data_extracted.append(row)

# Jika tidak ada data yang diekstrak, beri peringatan
if not data_extracted:
    raise ValueError("Gagal mengekstrak data. Pastikan format faktur sesuai.")

# Konversi ke DataFrame
columns = ["No FP", "Nama Penjual", "Nama Pembeli"] + [f"Kolom {i}" for i in range(4, len(data_extracted[0]) + 1)]
df = pd.DataFrame(data_extracted, columns=columns[:len(data_extracted[0])])

# Simpan ke dalam file Excel
output_excel = "/mnt/data/output.xlsx"
df.to_excel(output_excel, index=False)

print(f"Data berhasil diekstrak dan disimpan di {output_excel}")
