import pdfplumber

pdf_path = "/mnt/data/FP Balai Diklat Keuangan Balikpapan BPPK - 00006065303.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages, 1):
        text = page.extract_text()
        print(f"\n==== Halaman {page_num} ====\n")
        print(text)
        print("\n==============================\n")
