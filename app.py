import pdfplumber
import pandas as pd

# Path file PDF yang diunggah
pdf_path = "/mnt/data/FP Balai Diklat Keuangan Balikpapan BPPK - 00006065303.pdf"

# Membuka file PDF dan mencoba membaca semua tabel di dalamnya
data_extracted = []

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                # Filter hanya baris yang memiliki cukup data
                if len(row) > 1 and row[0] and row[1]:
                    data_extracted.append(row)

# Konversi ke DataFrame untuk kemudahan manipulasi
df = pd.DataFrame(data_extracted)

# Simpan ke dalam file Excel
output_excel = "/mnt/data/output.xlsx"
df.to_excel(output_excel, index=False, header=False)

print(f"Data berhasil diekstrak dan disimpan di {output_excel}")
