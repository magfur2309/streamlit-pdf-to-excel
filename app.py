import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
from datetime import datetime

# Simpan daftar password yang sedang digunakan
active_sessions = {}

demo_user = "demo"
demo_password = "demo123"
demo_upload_limit = 30
if "demo_upload_count" not in st.session_state:
    st.session_state["demo_upload_count"] = 0

def submit_auth():
    """Fungsi untuk menangani submit dengan Enter."""
    password = st.session_state["password"]
    username = st.session_state["username"]
    
    if username == demo_user and password == demo_password:
        if st.session_state["demo_upload_count"] >= demo_upload_limit:
            st.error("Akun demo telah mencapai batas unggahan. Minta akses tambahan.")
        else:
            st.session_state["authorized"] = True
            st.success("Login sebagai demo berhasil! Anda bisa mengunggah hingga 30 file.")
    elif password == "admin123":  # Ganti dengan kode yang lebih aman
        if password in active_sessions:
            st.error("Kode ini sudah digunakan oleh pengguna lain.")
        else:
            active_sessions[password] = username
            st.session_state["authorized"] = True
            st.success("Otorisasi berhasil! Anda dapat menggunakan aplikasi.")
    else:
        st.error("Kode salah! Coba lagi.")

def authenticate():
    """Fungsi untuk otorisasi pengguna dengan password unik untuk satu user."""
    if "authorized" not in st.session_state:
        st.session_state["authorized"] = False
    
    if not st.session_state["authorized"]:
        st.warning("Aplikasi ini memerlukan persetujuan sebelum digunakan.")
        st.text_input("Masukkan nama pengguna:", key="username")
        st.text_input("Masukkan kode otorisasi:", type="password", key="password", on_change=submit_auth)
        
        if st.button("Submit"):
            submit_auth()
        
        return False
    return True

def extract_data_from_pdf(pdf_file, existing_faktur):
    """
    Fungsi untuk mengekstrak data dari file PDF dan mengonversinya ke format tabel,
    menangani banyak halaman dan beberapa tabel dalam satu file.
    """
    data = []
    faktur_counter = 1
    tanggal_faktur = None
    nama_penjual = None
    nama_pembeli = None
    no_fp = None
    
    month_mapping = {
        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
    }
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                no_fp_match = re.search(r'Kode dan Nomor Seri Faktur Pajak:\s*(\d+)', text)
                if no_fp_match:
                    no_fp = no_fp_match.group(1)
                
                date_match = re.search(r'\b(\d{1,2})\s+(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+(\d{4})\b', text)
                if date_match:
                    day, month, year = date_match.groups()
                    tanggal_faktur = f"{year}-{month_mapping[month]}-{day.zfill(2)}"
                
                if no_fp and no_fp in existing_faktur and existing_faktur[no_fp] != tanggal_faktur:
                    st.error(f"Nomor faktur {no_fp} memiliki tanggal berbeda sebelumnya: {existing_faktur[no_fp]}")
                    continue
                
                existing_faktur[no_fp] = tanggal_faktur
                
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
                        nama_barang = row[2].replace("\n", " ").strip()
                        harga, qty, unit = 0, 0, "Unknown"
                        total = harga * qty
                        dpp = total / 1.11
                        ppn = total - dpp
                        
                        data.append([no_fp, nama_penjual, nama_pembeli, nama_barang, harga, unit, qty, total, dpp, ppn, tanggal_faktur])
                    
        faktur_counter += 1
    
    return data

st.title("Konversi Faktur Pajak PDF ke Excel")

if authenticate():
    uploaded_files = st.file_uploader("Upload Faktur Pajak (PDF, bisa lebih dari satu)", type=["pdf"], accept_multiple_files=True)
    
    if uploaded_files:
        if st.session_state["username"] == demo_user:
            if st.session_state["demo_upload_count"] + len(uploaded_files) > demo_upload_limit:
                st.error("Batas unggahan akun demo tercapai. Minta akses tambahan.")
            else:
                st.session_state["demo_upload_count"] += len(uploaded_files)
        
        all_data = []
        existing_faktur = {}
        
        for uploaded_file in uploaded_files:
            extracted_data = extract_data_from_pdf(uploaded_file, existing_faktur)
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
                writer.close()
            output.seek(0)
            st.download_button(label="\ud83d\udcbe Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
