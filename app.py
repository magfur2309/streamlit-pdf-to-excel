import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
import hashlib
import datetime

# Simpan user dengan password yang di-hash
users = {
    "admin": hashlib.sha256("password123".encode()).hexdigest(),
    "demo": hashlib.sha256("demo123".encode()).hexdigest()
}

# Simpan jumlah upload user demo
if "upload_count" not in st.session_state:
    st.session_state["upload_count"] = {}

# Fungsi untuk login
def login_page():
    st.title("Login Konversi Faktur Pajak")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if username in users and users[username] == hashed_password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["upload_count"].setdefault(username, 0)
            st.rerun()
        else:
            st.error("Username atau password salah")

# Fungsi utama aplikasi
def main_app():
    st.title("Konversi Faktur Pajak PDF to Excel")
    username = st.session_state["username"]

    # Batasi upload jika user adalah demo
    if username == "demo":
        today = datetime.date.today().isoformat()
        user_uploads = st.session_state["upload_count"].get(username, 0)

        if user_uploads >= 1:
            st.warning("User demo hanya bisa mengunggah **1 PDF per hari**.")
            return

    uploaded_files = st.file_uploader("Upload Faktur Pajak (PDF)", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        if username == "demo" and len(uploaded_files) > 1:
            st.error("User demo hanya bisa mengunggah **1 file per hari**.")
            return

        all_data = []
        for uploaded_file in uploaded_files:
            tanggal_faktur = find_invoice_date(uploaded_file)
            detected_item_count = count_items_in_pdf(uploaded_file)
            extracted_data = extract_data_from_pdf(uploaded_file, tanggal_faktur, detected_item_count)
            
            if extracted_data:
                all_data.extend(extracted_data)

        if all_data:
            df = pd.DataFrame(all_data, columns=[
                "No FP", "Nama Penjual", "Nama Pembeli", "Tanggal Faktur", "Nama Barang",
                "Qty", "Satuan", "Harga", "Potongan Harga", "Total", "DPP", "PPN"
            ])
            df.index = df.index + 1  
            
            st.write("### Pratinjau Data yang Diekstrak")
            st.dataframe(df)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=True, sheet_name='Faktur Pajak')
            output.seek(0)
            
            st.download_button(label="\U0001F4E5 Unduh Excel", data=output, file_name="Faktur_Pajak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            # Update upload count untuk user demo
            if username == "demo":
                st.session_state["upload_count"][username] = 1
        else:
            st.error("Gagal mengekstrak data. Pastikan format faktur sesuai.")

if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
    else:
        main_app()
