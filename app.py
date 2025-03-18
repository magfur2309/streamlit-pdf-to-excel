import streamlit as st
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_file):
    doc = fitz.open(pdf_file)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text

st.title("Pembaca Faktur PDF")

uploaded_file = st.file_uploader("Unggah file PDF", type=["pdf"])

if uploaded_file is not None:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    extracted_text = extract_text_from_pdf("temp.pdf")

    # Tampilkan teks yang diekstrak untuk debugging
    st.subheader("Teks yang Diekstrak dari PDF:")
    st.text_area("Teks PDF:", extracted_text, height=300)

