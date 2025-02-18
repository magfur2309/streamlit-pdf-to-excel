import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def check_login():
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username", key="username")
    password = st.sidebar.text_input("Password", type="password", key="password")
    
    if st.sidebar.button("Login"):
        if (username == "admin" and password == "admin") or (username == "demo" and password == "demo"):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["upload_count"] = 0  # Reset upload count saat login baru
            st.sidebar.success(f"Login berhasil sebagai {username}")
        else:
            st.sidebar.error("Username atau password salah")

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
        for page in pdf.pages:
            text = page.extract_text()
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
            
            table = page.extract_table()
            if table:
                previous_row = None
                for row in table:
                    if len(row) >= 4 and row[0].isdigit():
                        if previous_row and row[0] == "":
                            previous_row[2] += " " + " ".join(row[2].split("\n")).strip()
                            continue
                        
                        cleaned_lines = [line for line in row[2].split("\n") if not re.search(r'Rp\s[\d,.]+|PPnBM|Potongan Harga', line)]
                        nama_barang = " ".join(cleaned_lines).strip()
                        
                        harga_qty_info = re.search(r'Rp ([\d.,]+) x ([\d.,]+) (\w+)', row[2])
                        if harga_qty_info:
                            harga = int(float(harga_qty_info.group(1).replace('.', '').replace(',', '.')))
                            qty = int(float(harga_qty_info.group(2).replace('.', '').replace(',', '.')))
                            unit = harga_qty_info.group(3)
                        else:
                            harga, qty, unit = 0, 0, "Unknown"
                        
                        total = harga * qty
                        dpp = total / 1.11
                        ppn = total - dpp
                        
                        item = [
                            no_fp if no_fp else "Tidak ditemukan", 
                            nama_penjual if nama_penjual else "Tidak ditemukan", 
                            nama_pembeli if nama_pembeli else "Tidak ditemukan", 
                            nama_barang, harga, unit, qty, total, dpp, ppn, 
                            tanggal_faktur  
                        ]
                        data.append(item)
                        previous_row = item
    return data

st.title("Konversi Faktur Pajak PDF ke Excel")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

check_login()

if st.session_state["logged_in"]:
    if st.session_state["username"] == "demo" and st.session_state["upload_count"] >= 15:
        st.error("Batas upload tercapai! Sesi berakhir.")
        st.session_state["logged_in"] = False
    else:
        uploaded_files = st.file_uploader("Upload Faktur Pajak (PDF, bisa lebih dari satu)", type=["pdf"], accept_multiple_files=True)
        if uploaded_files:
            all_data = []
            for uploaded_file in uploaded_files:
                if st.session_state["username"] == "demo":
                    st.session_state["upload_count"] += 1
                    if st.session_state["upload_count"] > 15:
                        st.error("Batas upload tercapai! Sesi berakhir.")
                        st.session_state["logged_in"] = False
                        st.stop()
                tanggal_faktur = extract_tanggal_faktur(uploaded_file)  
                extracted_data = extract_data_from_pdf(uploaded_file, tanggal_faktur)
                if extracted_data:
                    all_data.extend(extracted_data)
            if all_data:
                df = pd.DataFrame(all_data, columns=["No FP", "Nama Penjual", "Nama Pembeli", "Nama Barang", "Harga", "Unit", "QTY", "Total", "DPP", "PPN", "Tanggal Faktur"])
                df.index = df.index + 1  
                st.write("### Pratinjau Data yang Diekstrak")
                st.dataframe(df)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=True, sheet_name='Faktur Pajak')
                output.seek(0)
                st.download_button(label="📥 Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
else:
    st.warning("Silakan login terlebih dahulu.")
