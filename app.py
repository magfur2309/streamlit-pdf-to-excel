import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def check_login():
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username", key="username")
    password = st.sidebar.text_input("Password", type="password", key="password")
    
    if st.sidebar.text_input("Tekan Enter untuk Login", key="login_enter", on_change=lambda: login(username, password)):
        pass
    
    if st.sidebar.button("Login"):
        login(username, password)

def login(username, password):
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

st.title("Konversi Faktur Pajak PDF ke Excel")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

check_login()

if st.session_state["logged_in"]:
    st.write("Selamat datang, Anda telah login!")
else:
    st.warning("Silakan login terlebih dahulu.")
