import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

# Simpan akun & password dalam dictionary
USERS = {
    "admin": "admin",
    "demo": "123456"
}

# Maksimum upload untuk user demo
MAX_UPLOADS_DEMO = 20

# Inisialisasi session state untuk login & limit upload
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.upload_count = 0  # Hanya untuk user demo

# Halaman login
def login_page():
    st.title("Login Page")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        if username in USERS and USERS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            if username == "demo":
                st.session_state.upload_count = 0  # Reset counter untuk perangkat baru
            st.success(f"Login berhasil sebagai {username}")
            st.experimental_rerun()
        else:
            st.error("Username atau password salah!")

# Jika belum login, tampilkan halaman login
if not st.session_state.logged_in:
    login_page()
    st.stop()

# Jika sudah login, tampilkan aplikasi utama
st.title("Konversi Faktur Pajak PDF ke Excel")

if st.session_state.username == "demo" and st.session_state.upload_count >= MAX_UPLOADS_DEMO:
    st.error("Akun demo telah mencapai batas maksimal upload (20 PDF). Silakan login dari perangkat lain atau gunakan akun admin.")
    st.stop()

uploaded_files = st.file_uploader("Upload Faktur Pajak (PDF, bisa lebih dari satu)", type=["pdf"], accept_multiple_files=True)

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
                for row in table:
                    if len(row) >= 4 and row[0].isdigit():
                        nama_barang = " ".join(row[2].split("\n")).strip()
                        harga, qty, unit = 0, 0, "Unknown"
                        item = [
                            no_fp if no_fp else "Tidak ditemukan", 
                            nama_penjual if nama_penjual else "Tidak ditemukan", 
                            nama_pembeli if nama_pembeli else "Tidak ditemukan", 
                            nama_barang, harga, unit, qty, 0, 0, 0, 
                            tanggal_faktur  
                        ]
                        data.append(item)
    return data

if uploaded_files:
    if st.session_state.username == "demo":
        if st.session_state.upload_count + len(uploaded_files) > MAX_UPLOADS_DEMO:
            st.error("Melebihi batas maksimal upload untuk akun demo.")
            st.stop()
        st.session_state.upload_count += len(uploaded_files)
    
    all_data = []
    
    for uploaded_file in uploaded_files:
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

if st.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.upload_count = 0
    st.experimental_rerun()
