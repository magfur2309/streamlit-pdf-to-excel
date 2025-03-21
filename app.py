import PyPDF2
import pandas as pd

# Fungsi untuk membaca data dari file PDF
def extract_data_from_pdf(pdf_file_path):
    # Membuka file PDF
    with open(pdf_file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        
        # Menyusun teks dari setiap halaman dalam PDF
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    
    return text

# Fungsi untuk mengonversi teks ke format tabel
def convert_to_table(text):
    # Pisahkan data berdasarkan nomor urut dan barang
    lines = text.splitlines()
    data = []
    item_start = False
    for line in lines:
        # Jika menemukan bagian dengan data barang, mulai proses pengambilan data
        if line.strip().startswith('No.'):
            item_start = True
            continue
        if item_start:
            parts = line.split(" - ")
            if len(parts) > 1:
                no_urut = parts[0].strip()
                barang = " - ".join(parts[1:]).strip()
                data.append([no_urut, barang])
    
    # Membuat dataframe menggunakan pandas
    df = pd.DataFrame(data, columns=["No Urut", "Barang"])
    return df

# Fungsi utama untuk mengonversi PDF ke tabel
def convert_pdf_to_table(pdf_file_path):
    text = extract_data_from_pdf(pdf_file_path)
    table = convert_to_table(text)
    return table

# Path file PDF yang akan diproses
pdf_file_path = 'OutputTaxInvoice-8316ab33-870d-4ba3-b65a-18a7dcaa85d2-0960088649086000-04002500037469724--.pdf'

# Melakukan konversi
table = convert_pdf_to_table(pdf_file_path)

# Menampilkan hasil konversi
print(table)

# Jika ingin menyimpan ke file CSV
table.to_csv('output_barang.csv', index=False)
