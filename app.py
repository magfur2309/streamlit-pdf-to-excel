import os
import pdfplumber
import pandas as pd
from itertools import zip_longest

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
            continue  # Lewati halaman ini jika tidak ada tabel
        for table in tables:
            for row in table:
                if any(row):  # Hanya tambahkan baris yang memiliki setidaknya satu data
                    data_extracted.append(row)

# Jika tidak ada data yang diekstrak, beri peringatan
if not data_extracted:
    raise ValueError("Gagal mengekstrak data. Pastikan format faktur sesuai.")

# Menyamakan panjang kolom agar tidak terjadi error "list index out of range"
max_columns = max(len(row) for row in data_extracted)
data_extracted = [list(row) + [''] * (max_columns - len(row)) for row in data_extracted]

# Konversi ke DataFrame
columns = ["No FP", "Nama Penjual", "Nama Pembeli"] + [f"Kolom {i}" for i in range(4, max_columns + 1)]
df = pd.DataFrame(data_extracted, columns=columns[:max_columns])

# Simpan ke dalam file Excel
output_excel = "/mnt/data/output.xlsx"
df.to_excel(output_excel, index=False)

print(f"Data berhasil diekstrak dan disimpan di {output_excel}")
