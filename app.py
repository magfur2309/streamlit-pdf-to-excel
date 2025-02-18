import pdfplumber

def extract_first_row_per_column(pdf_path):
    extracted_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                # Periksa jika tabel memiliki data
                if table and len(table) > 1:
                    first_row = table[1]  # Baris pertama setelah header
                    nama_barang_index = None
                    
                    # Cari indeks kolom Nama Barang
                    header = table[0]
                    for i, col_name in enumerate(header):
                        if col_name and "Barang" in col_name:
                            nama_barang_index = i
                            break
                    
                    # Jika ditemukan, simpan data
                    if nama_barang_index is not None and nama_barang_index < len(first_row):
                        nama_barang = first_row[nama_barang_index]
                        extracted_data.append(nama_barang)
    
    return extracted_data

# Ganti dengan path ke file PDF yang diunggah
pdf_path = "/mnt/data/OutputTaxInvoice-8316ab33-870d-4ba3-b65a-18a7dcaa85d2-0960088649086000-04002500037469724--.pdf"
result = extract_first_row_per_column(pdf_path)

# Cetak hasil
for i, barang in enumerate(result, 1):
    print(f"{i}. {barang}")
