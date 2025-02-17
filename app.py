import pdfplumber
import re
import pandas as pd

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF dan mengonversinya ke format tabel.
    """
    data = []
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                try:
                    # Ekstrak informasi dasar
                    no_fp = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', text)
                    nama_penjual = re.search(r'Pengusaha Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                    nama_pembeli = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*(.+)', text)

                    # Menangkap semua barang/jasa yang ada di faktur
                    barang_pattern = re.findall(r'\d+\s+(\d+)\s+([\w\s]+)\s+Rp ([\d.,]+)\s+x\s+([\d.,]+)\s+Piece', text)
                    
                    if not barang_pattern:
                        continue  # Jika tidak ada barang, skip halaman ini

                    for match in barang_pattern:
                        kode_barang, barang, harga_satuan, qty = match
                        harga = int(float(harga_satuan.replace('.', '').replace(',', '.')))
                        qty = int(float(qty.replace('.', '').replace(',', '.')))
                        unit = "Piece"
                        total = harga * qty

                        # Simpan ke data list
                        data.append([
                            no_fp.group(1) if no_fp else "",
                            nama_penjual.group(1).strip() if nama_penjual else "",
                            nama_pembeli.group(1).strip() if nama_pembeli else "",
                            barang.strip(),
                            harga,
                            unit,
                            qty,
                            total
                        ])

                except Exception as e:
                    print(f"Terjadi kesalahan dalam membaca halaman: {e}")
    
    return data

# Contoh penggunaan
pdf_path = "/mnt/data/FP Balai Diklat Keuangan Balikpapan BPPK - 00006065303.pdf"
data = extract_data_from_pdf(pdf_path)

# Simpan ke Excel
df = pd.DataFrame(data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Barang", "Harga Satuan", "Satuan", "Jumlah", "Total"])
df.to_excel("/mnt/data/output.xlsx", index=False)

print("Data berhasil diekstrak dan disimpan ke output.xlsx")
