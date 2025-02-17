import pdfplumber
import pandas as pd
import re

def extract_data_from_pdf(pdf_file):
    """
    Fungsi untuk mengekstrak data dari file PDF dan mengonversinya ke format tabel.
    """
    data = []
    full_text = ""

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    try:
        # Menangkap informasi faktur
        no_fp = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', full_text)
        nama_penjual = re.search(r'Pengusaha Kena Pajak:\s*Nama\s*:\s*(.+)', full_text)
        nama_pembeli = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*(.+)', full_text)

        # Menangkap informasi barang
        barang_regex = re.findall(r'(\d{1,2})\s+000000\s+(.+?)\s+Rp ([\d.,]+) x ([\d.,]+) Piece', full_text)

        for match in barang_regex:
            nomor, barang, harga, qty = match

            harga = int(float(harga.replace('.', '').replace(',', '.')))
            qty = int(float(qty.replace('.', '').replace(',', '.')))
            total = harga * qty

            # Struktur data sesuai format tabel yang diinginkan
            data.append([
                no_fp.group(1) if no_fp else "",  # No Faktur
                nama_penjual.group(1).strip() if nama_penjual else "",  # Nama Penjual
                nama_pembeli.group(1).strip() if nama_pembeli else "",  # Nama Pembeli
                barang.strip(),  # Barang
                harga,  # Harga
                "Piece",  # Unit
                qty,  # QTY
                total,  # Total
                "",  # DPP (Opsional, bisa diisi jika ada regex yang menangkapnya)
                "",  # PPN (Opsional, bisa diisi jika ada regex yang menangkapnya)
                ""   # Tanggal Faktur (Opsional)
            ])

    except Exception as e:
        print(f"Terjadi kesalahan dalam membaca file: {e}")

    return data

# Contoh pemrosesan PDF
pdf_file_path = "OutputTaxInvoice.pdf"  # Ubah sesuai dengan lokasi file
all_data = extract_data_from_pdf(pdf_file_path)

# Buat DataFrame dengan susunan kolom yang sesuai
df = pd.DataFrame(all_data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Barang", "Harga", "Unit", "QTY", "Total", "DPP", "PPN", "Tanggal Faktur"])

# Tambahkan kolom "No" sebagai nomor urut di paling kiri
df.insert(0, "No", range(1, len(df) + 1))

# Simpan hasil ke Excel
df.to_excel("output.xlsx", index=False)

print("Proses ekstraksi selesai. File telah disimpan sebagai output.xlsx")
