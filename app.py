import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

# Dummy user database (For demo purposes)
USER_CREDENTIALS = {
    "admin": "password",  # Super Admin account
    "demo": "demo"      # Demo User account
}

# Function to check if user is logged in
def check_login(username, password):
    if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
        return True
    return False

# Function to extract date (Tanggal Faktur)
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

# Function to extract data from PDF
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
                        
                        nama_barang = " ".join(row[2].split("\n")).strip()
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

# Streamlit UI
st.title("Konversi Faktur Pajak PDF ke Excel")

# Check if user is logged in
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False  # Initialize the session state

# If user is not logged in, show the login form
if not st.session_state["logged_in"]:
    with st.form(key='login_form'):
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")
        
        if login_button:
            if check_login(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["is_super_admin"] = username == "super_admin"  # Check if the user is super admin
                st.success(f"Welcome, {username}!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")
else:
    # User is logged in, show the main functionality
    is_demo_user = st.session_state["username"] == "demo_user"
    uploaded_files = st.file_uploader("Upload Faktur Pajak (PDF, bisa lebih dari satu)", type=["pdf"], accept_multiple_files=True)

    if is_demo_user:
        if len(uploaded_files) > 50:
            st.error("Demo user can only upload a maximum of 50 files.")
        else:
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
                    writer.close()
                output.seek(0)
                
                st.download_button(label="📥 Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
    
    elif st.session_state["is_super_admin"]:
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
                writer.close()
            output.seek(0)
            
            st.download_button(label="📥 Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
