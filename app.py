import streamlit as st
import pandas as pd
import pdfplumber
import io

st.title("Konversi PDF ke Excel")
uploaded_files = st.file_uploader("Upload file PDF", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for uploaded_file in uploaded_files:
        with pdfplumber.open(uploaded_file) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            all_data.append({"Filename": uploaded_file.name, "Content": text})
    
    df = pd.DataFrame(all_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Data PDF")
    st.download_button(label="Download Excel", data=output.getvalue(), file_name="output.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
