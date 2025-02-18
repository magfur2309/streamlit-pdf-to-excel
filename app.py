import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
import uuid

# Initialize session state variables
if 'upload_count' not in st.session_state:
    st.session_state['upload_count'] = 0

if 'user_authenticated' not in st.session_state:
    st.session_state['user_authenticated'] = False

if 'username' not in st.session_state:
    st.session_state['username'] = None

if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())  # Generate a unique session ID

# Function to check if the user has exceeded the upload limit
def check_upload_limit():
    if st.session_state.get('username') == 'demo' and st.session_state['upload_count'] >= 50:
        st.warning("Anda sudah melebihi batas maksimal penggunaan untuk demo account (50 file).")
        return True
    return False

# Function to handle user login
def login(username, password):
    # Dummy user credentials for admin and demo
    users = {
        "admin": "123456",
        "demo": "123456"
    }

    # Check if the credentials match
    if username in users and users[username] == password:
        st.session_state['user_authenticated'] = True
        st.session_state['username'] = username
        st.session_state['upload_count'] = 0  # Reset upload count when logged in (for demo user on a new device)
        return True
    return False

# Display login form if user is not authenticated
if not st.session_state['user_authenticated']:
    # Form layout for login
    with st.form(key="login_form"):
        st.title("Login untuk Mengakses Aplikasi")

        # Form fields
        username = st.text_input("Username", placeholder="Masukkan username Anda")
        password = st.text_input("Password", type="password", placeholder="Masukkan password Anda")
        
        # Submit button
        submit_button = st.form_submit_button(label="Login")

        # Login logic
        if submit_button:
            if login(username, password):
                st.success(f"Selamat datang, {username}!")
            else:
                st.error("Username atau password salah. Coba lagi.")
else:
    # Main application code after login

    # Check upload limit for demo users
    if check_upload_limit():
        st.stop()  # Stop the process if the demo user has exceeded the upload limit

    # Main Application: PDF Upload and Processing
    st.title("Konversi Faktur Pajak PDF ke Excel")

    # File uploader for PDF invoices
    uploaded_files = st.file_uploader("Upload Faktur Pajak (PDF, bisa lebih dari satu)", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
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
            
            # Increment the upload count for demo user
            if st.session_state['username'] == 'demo':
                st.session_state['upload_count'] += len(uploaded_files)
        else:
            st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")
