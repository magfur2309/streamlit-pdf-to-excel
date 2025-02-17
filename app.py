import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import io
import re

def extract_text_with_ocr(pdf_file):
    """
    Ekstrak teks dari PDF menggunakan OCR jika teks tidak bisa dibaca langsung.
    """
    extracted_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:  # Jika teks kosong, gunakan OCR
                image = page.to_image()
                text = pytesseract.image_to_string(image.original)
            extracted_text += text + "\n"
    return extracted_text

# Streamlit UI
st.title("Konversi Faktur Pajak PDF ke Excel dengan OCR")

uploaded_file = st.file_uploader("Upload Faktur Pajak (PDF)", type=["pdf"])

if uploaded_file:
    extracted_text = extract_text_with_ocr(uploaded_file)
    if extracted_text.strip():
        st.text_area("Hasil Ekstraksi Teks", extracted_text, height=300)
    else:
        st.error("Gagal mengekstrak teks dari PDF.")
