import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def extract_tanggal_faktur(pdf):
    month_mapping = {
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
    }
    tanggal_faktur = "Tidak ditemukan"
    
    with pdfplumber.open(pdf) as pdf_obj:
        for page in pdf_obj.pages:
            text = page.extract_text()
            if text:
                date_match = re.search(r'(\d{1,2})\s*(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s*(\d{4})', text, re.IGNORECASE)
                if date_match:
                    day, month, year = date_match.groups()
                    tanggal_faktur = f"{year}-{month_mapping[month]}-{day.zfill(2)}"
                    break  
    
    return tanggal_faktur

def extract_data_from_pdf(pdf_file, tanggal_faktur):
    data = []
    no_fp, nama_penjual, nama_pembeli = None, None, None

    with pdfplumber.open(pdf_file) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            st.write(f"### Page {page_number} Text Extracted:")
            st.text(text)  # Show extracted text for debugging
            
            if text:
                no_fp_match = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', text)
                if no_fp_match:
                    no_fp = no_fp_match.group(1)
                
                penjual_match = re.search(r'Nama\s*:\s*([\w\s\-.,&]+)\nAlamat', text)
                if penjual_match:
                    nama_penjual = penjual_match.group(1).strip()
                
                pembeli_match = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*([\w\s\-.,&]+)\nAlamat', text)
                if pembeli_match:
                    nama_pembeli = pembeli_match.group(1).strip()
            
            # Extract table data from the page
            table = page.extract_table()
            st.write(f"### Page {page_number} Table Extracted:")
            st.write(table)  # Show extracted table for debugging

            if table:
                # Find the index of the "No." column in the table
                header = table[0]
                no_col_index = None
                for i, column in enumerate(header):
                    if column and "No." in column:  # Detect "No." column
                        no_col_index = i
                        break
                
                if no_col_index is not None:
                    # Extract rows based on the "No." column
                    for row in table[1:]:  # Skip the header row
                        if len(row) > no_col_index:  # Ensure it's a valid row
                            no_urut = row[no_col_index]
                            nama_barang = " ".join(row[2].split("\n")).strip() if len(row) > 2 else "Unknown"
                            
                            harga_qty_info = re.search(r'Rp ([\d.,]+) x ([\d.,]+) (\w+)', row[2]) if len(row) > 2 else None
                            if harga_qty_info:
                                harga = int(float(harga_qty_info.group(1).replace('.', '').replace(',', '.')))
                                qty = int(float(harga_qty_info.group(2).replace('.', '').replace(',', '.')))
                                unit = harga_qty_info.group(3)
                            else:
                                harga, qty, unit = 0, 0, "Unknown"
                            
                            total = harga * qty
                            dpp = total / 1.11
                            ppn = total - dpp
                            
                            # Add data for this item
                            item = [
                                no_fp if no_fp else "Tidak ditemukan", 
                                nama_penjual if nama_penjual else "Tidak ditemukan", 
                                nama_pembeli if nama_pembeli else "Tidak ditemukan", 
                                nama_barang, harga, unit, qty, total, dpp, ppn, 
                                tanggal_faktur  
                            ]
                            data.append(item)
                else:
                    st.error(f"Column 'No.' not found on page {page_number}")
    return data

st.title("Konversi Faktur Pajak PDF ke Excel")

# Store the uploaded files in session state
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []

uploaded_files = st.file_uploader("Upload Faktur Pajak (PDF, bisa lebih dari satu)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    # Clear previous data when new files are uploaded
    st.session_state["uploaded_files"] = uploaded_files
    all_data = []
    
    for uploaded_file in st.session_state["uploaded_files"]:
        tanggal_faktur = extract_tanggal_faktur(uploaded_file)  
        extracted_data = extract_data_from_pdf(uploaded_file, tanggal_faktur)
        if extracted_data:
            all_data.extend(extracted_data)
    
    if all_data:
        df = pd.DataFrame(all_data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Nama Barang", "Harga", "Unit", "QTY", "Total", "DPP", "PPN", "Tanggal Faktur"])
        df.index = df.index + 1  # Set index starting from 1
        
        # Display the extracted data preview
        st.write("### Pratinjau Data yang Diekstrak")
        st.dataframe(df)
        
        # Save the data as an Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=True, sheet_name='Faktur Pajak')
            writer.close()
        output.seek(0)
        
        # Add download button for the Excel file
        st.download_button(label="📥 Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
