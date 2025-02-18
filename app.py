import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def check_login():
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username", key="username")
    password = st.sidebar.text_input("Password", type="password", key="password")
    
    if st.sidebar.text_input("Tekan Enter untuk Login", key="hidden_input", type="default") or st.sidebar.button("Login"):
        if (username == "admin" and password == "admin") or (username == "demo" and password == "demo"):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["upload_count"] = 0  # Reset upload count saat login baru
            st.sidebar.success(f"Login berhasil sebagai {username}")
        else:
            st.sidebar.error("Username atau password salah")

# Fungsi lainnya tetap sama...

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
