import pdfkit
import os

PDF_MAP = "pdf"


def ensure_pdf_map():
    if not os.path.exists(PDF_MAP):
        os.makedirs(PDF_MAP)


def generate_pdf(html_string, filename):
    ensure_pdf_map()

    path = os.path.join(PDF_MAP, filename)

    config = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )

    pdfkit.from_string(html_string, path, configuration=config)

    return path