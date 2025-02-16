import pdfplumber
import pandas as pd
import os
from tkinter import Tk, filedialog

def extract_data_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    
    # Contoh ekstraksi dengan regex (perlu disesuaikan dengan format faktur)
    import re
    faktur_match = re.search(r'Kode dan Nomor Seri Faktur Pajak: ([\d.-]+)', text)
    penjual_match = re.search(r'Pengusaha Kena Pajak\s+Nama: (.*?)\s+Alamat:', text, re.DOTALL)
    pembeli_match = re.search(r'Pembeli Barang Kena Pajak / Penerima Jasa Kena Pajak\s+Nama: (.*?)\s+Alamat:', text, re.DOTALL)
    barang_match = re.search(r'Nama Barang Kena Pajak / Jasa Kena Pajak\s+(.*?)\s+Harga', text, re.DOTALL)
    harga_match = re.search(r'Rp ([\d.,]+) x (\d+)', text)
    total_match = re.search(r'Harga Jual / Penggantian\s+([\d.,]+)', text)
    dpp_match = re.search(r'Dasar Pengenaan Pajak\s+([\d.,]+)', text)
    ppn_match = re.search(r'PPN = 10% x Dasar Pengenaan Pajak\s+([\d.,]+)', text)
    
    return {
        "no FP": faktur_match.group(1) if faktur_match else "",
        "Nama Penjual": penjual_match.group(1).strip() if penjual_match else "",
        "Nama Pembeli": pembeli_match.group(1).strip() if pembeli_match else "",
        "Barang": barang_match.group(1).strip() if barang_match else "",
        "Harga": harga_match.group(1).replace(',', '.') if harga_match else "",
        "Unit": "pcs",  # Asumsi default
        "QTY": harga_match.group(2) if harga_match else "",
        "Total": total_match.group(1).replace(',', '.') if total_match else "",
        "DPP": dpp_match.group(1).replace(',', '.') if dpp_match else "",
        "PPn": ppn_match.group(1).replace(',', '.') if ppn_match else ""
    }

def main():
    root = Tk()
    root.withdraw()
    file_paths = filedialog.askopenfilenames(title="Pilih file PDF", filetypes=[("PDF Files", "*.pdf")])
    
    data_list = []
    for file_path in file_paths:
        data_list.append(extract_data_from_pdf(file_path))
    
    df = pd.DataFrame(data_list)
    output_file = os.path.join(os.getcwd(), "output_faktur.xlsx")
    df.to_excel(output_file, index=False)
    print(f"Data berhasil disimpan ke {output_file}")

if __name__ == "__main__":
    main()
