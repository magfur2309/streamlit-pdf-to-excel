import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re  # Untuk pencarian pola teks

# Fungsi untuk mengekstrak teks dari PDF
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(pdf_file)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

# Fungsi untuk mengekstrak Nomor Faktur Pajak dari teks
def extract_no_fp(text):
    match = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*([\d]+)', text)
    if match:
        return match.group(1)
    return "Tidak ditemukan"

# Fungsi untuk mengekstrak Nama Barang dari bagian "Barang Kena Pajak / Jasa Kena Pajak"
def extract_barang(text):
    barang_list = []
    
    # Cari bagian yang berisi "Barang Kena Pajak / Jasa Kena Pajak"
    start_idx = text.find("Barang Kena Pajak / Jasa Kena Pajak")
    
    if start_idx != -1:
        # Potong teks setelah header
        text = text[start_idx:]
        lines = text.split("\n")

        for line in lines:
            parts = line.strip().split()
            if parts and parts[0].isdigit():  # Jika diawali angka, berarti nomor urut item
                nama_barang = " ".join(parts[1:])  # Ambil teks setelah nomor
                barang_list.append(nama_barang)

    return barang_list

# Fungsi untuk memproses data menjadi format tabel
def process_extracted_text(text):
    data = []
    lines = text.split("\n")

    no_fp = extract_no_fp(text)  # Ambil nomor faktur pajak
    daftar_barang = extract_barang(text)  # Ambil daftar barang

    item_index = 0  # Untuk melacak barang sesuai urutan
    
    for line in lines:
        parts = line.split()  # Memisahkan berdasarkan spasi/tab
        if len(parts) >= 9 and parts[0].isdigit():  # Pastikan format valid & ada nomor urut item
            nama_barang = daftar_barang[item_index] if item_index < len(daftar_barang) else "Tidak ditemukan"
            item_index += 1  # Pindah ke item berikutnya
            
            # Simpan data dalam format tabel
            data.append([no_fp] + parts[:4] + [nama_barang] + parts[4:])

    # Cek apakah ada data yang diekstrak sebelum membuat DataFrame
    if not data:
        return pd.DataFrame()  # Kembalikan DataFrame kosong jika tidak ada data

    # Kolom tabel sesuai dengan format yang diminta
    columns = ["No FP", "Nama Perusahaan", "Nama Pembeli", "Tanggal Faktur", "Nama Barang",
               "Qty", "Satuan", "Harga", "Potongan", "Total", "DPP", "PPN"]
    
    # Pastikan panjang kolom tidak melebihi jumlah elemen dalam data
    df = pd.DataFrame(data, columns=columns[:len(data[0])])

    return df


st.title("Ekstraksi Faktur Pajak dari PDF")

uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])

if uploaded_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    extracted_text = extract_text_from_pdf("temp.pdf")

    # Ambil Nomor Faktur Pajak
    no_fp = extract_no_fp(extracted_text)
    st.write(f"**Nomor Faktur Pajak yang Ditemukan:** {no_fp}")

    df = process_extracted_text(extracted_text)

    if not df.empty:
        st.subheader("Hasil Ekstraksi dalam Bentuk Tabel:")
        st.dataframe(df)  # Menampilkan tabel di Streamlit
        st.download_button("Unduh Data sebagai Excel", df.to_csv(index=False), "data.csv", "text/csv")
    else:
        st.warning("Tidak ada data yang ditemukan dalam PDF.")
