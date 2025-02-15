import os
import pdfplumber
import pandas as pd
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    return text

def parse_invoice_data(text):
    """
    Fungsi untuk mengambil data faktur pajak dari teks yang diekstrak.
    """
    try:
        lines = text.split("\n")
        invoice_data = {
            "No FP": "", "Nama Penjual": "", "Nama Pembeli": "",
            "Barang": "", "Harga": 0, "Unit": "", "QTY": 0,
            "Total": 0, "DPP": 0, "PPN": 0, "Tanggal Faktur": ""
        }
        
        for i, line in enumerate(lines):
            if "Kode dan Nomor Seri Faktur Pajak" in line:
                invoice_data["No FP"] = line.split(":")[-1].strip()
            elif "Nama:" in line and "UNIVERSAL BIG DATA" in line:
                invoice_data["Nama Penjual"] = "PT. UNIVERSAL BIG DATA"
            elif "Nama :" in line and "INDUSTRI" in line:
                invoice_data["Nama Pembeli"] = lines[i].split(":")[-1].strip()
            elif "Maintenance" in line or "Sewa User" in line:
                invoice_data["Barang"] = line.strip()
            elif "Rp" in line and "x" in line:
                harga_qty = line.split(" ")
                invoice_data["Harga"] = int(harga_qty[1].replace(",", ""))
                invoice_data["Unit"] = harga_qty[-1]
                invoice_data["QTY"] = int(harga_qty[-2].replace(",", ""))
            elif "Dasar Pengenaan Pajak" in line:
                invoice_data["DPP"] = int(lines[i+1].replace(",", ""))
            elif "Jumlah PPN" in line:
                invoice_data["PPN"] = int(lines[i+1].replace(",", ""))
            elif "KOTA MALANG" in line:
                invoice_data["Tanggal Faktur"] = lines[i+1].strip()
                
        invoice_data["Total"] = invoice_data["Harga"] * invoice_data["QTY"]
        return invoice_data
    except Exception as e:
        print(f"Error parsing invoice data: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def upload_files():
    if request.method == "POST":
        files = request.files.getlist("files")
        extracted_data = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                
                text = extract_text_from_pdf(filepath)
                invoice_data = parse_invoice_data(text)
                if invoice_data:
                    extracted_data.append(invoice_data)
        
        if extracted_data:
            df = pd.DataFrame(extracted_data)
            output_file = "faktur_pajak.xlsx"
            df.to_excel(output_file, index=False)
            return send_file(output_file, as_attachment=True)
        else:
            return "Gagal mengekstrak data faktur pajak."
    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True)
