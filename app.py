import fitz  # PyMuPDF
import pandas as pd
import re

def extract_invoice_data(pdf_path):
    # Buka file PDF
    doc = fitz.open(pdf_path)
    
    # Variabel untuk menyimpan hasil ekstraksi
    invoice_data = []
    
    # Pola regex untuk menangkap detail transaksi, termasuk No. 33
    pattern = re.compile(r"(\d+)\s+600600\s+([\w\s,.-]+)SJ: ([\w\d]+), Tanggal:\s+(\d{2}/\d{2}/\d{4})\s+Rp ([\d.,]+) x ([\d.,]+) Kilogram\s+Potongan Harga = Rp ([\d.,]+)\s+PPnBM \(0,00%\) = Rp ([\d.,]+)\s+([\d.,]+)")
    
    # Loop setiap halaman PDF
    for page in doc:
        text = page.get_text("text")
        text = text.replace("\n", " ")  # Pastikan format teks konsisten
        matches = pattern.findall(text)
        
        for match in matches:
            invoice_data.append({
                "No": int(match[0]),
                "Kode Barang": "600600",
                "Nama Barang": match[1].strip(),
                "SJ": match[2],
                "Tanggal": match[3],
                "Harga per Kg (Rp)": match[4],
                "Jumlah (Kg)": match[5],
                "Potongan Harga (Rp)": match[6],
                "PPnBM (Rp)": match[7],
                "Total Harga (Rp)": match[8]
            })
    
    # Konversi ke DataFrame Pandas
    df = pd.DataFrame(invoice_data)
    
    return df

# Contoh penggunaan
pdf_path = "FP_GEMILANG.pdf"  # Ganti dengan path file PDF Anda
df_result = extract_invoice_data(pdf_path)

# Tampilkan hasil
print(df_result)

# Simpan ke Excel (opsional)
df_result.to_excel("Hasil_Ekstraksi.xlsx", index=False)
