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
                    no_fp = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', text)
                    nama_penjual = re.search(r'Pengusaha Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                    nama_pembeli = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*(.+)', text)

                    # Menangkap semua barang/jasa yang ada di faktur
                    barang_pattern = re.findall(r'(\d+)\s+(.+?)\s+Rp ([\d.,]+)\s+x\s+([\d.,]+)\s+Bulan', text)
                    
                    if not barang_pattern:
                        continue  # Jika tidak ada barang, skip halaman ini

                    for match in barang_pattern:
                        kode_barang, barang, harga_satuan, qty = match
                        harga = int(float(harga_satuan.replace('.', '').replace(',', '.')))
                        qty = int(float(qty.replace('.', '').replace(',', '.')))
                        unit = "Bulan"
                        total = harga * qty

                        # Simpan ke data list
                        data.append([no_fp.group(1) if no_fp else "",
                                     nama_penjual.group(1).strip() if nama_penjual else "",
                                     nama_pembeli.group(1).strip() if nama_pembeli else "",
                                     barang.strip(), harga, unit, qty, total])

                except Exception as e:
                    st.error(f"Terjadi kesalahan dalam membaca halaman: {e}")
    return data
