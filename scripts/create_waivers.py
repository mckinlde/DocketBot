# scripts/create_waivers.py

import os
import sys
import json
import datetime
import threading
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from io import BytesIO

def load_config():
    config_path = os.path.join(os.environ["LOCALAPPDATA"], "DocketBot", "config.json")
    with open(config_path, "r") as f:
        return json.load(f)

def generate_overlay(signature_path, client_name, case_number):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Example positions — adjust to match your waiver PDF template
    can.drawString(100, 650, f"Client: {client_name}")
    can.drawString(100, 630, f"Case: {case_number}")
    can.drawString(100, 610, f"Date: {datetime.date.today().strftime('%Y-%m-%d')}")

    if os.path.isfile(signature_path):
        try:
            img = ImageReader(signature_path)
            can.drawImage(img, 100, 560, width=150, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"[ERROR] Failed to embed signature: {e}")

    can.save()
    packet.seek(0)
    return PdfReader(packet)

def create_waiver_page(template_path, signature_path, client_name, case_number):
    try:
        base_pdf = PdfReader(template_path)
        overlay_pdf = generate_overlay(signature_path, client_name, case_number)

        writer = PdfWriter()
        page = base_pdf.pages[0]
        page.merge_page(overlay_pdf.pages[0])
        writer.add_page(page)

        output = BytesIO()
        writer.write(output)
        output.seek(0)
        return PdfReader(output).pages[0]
    except Exception as e:
        print(f"[ERROR] Failed to create waiver for {client_name} / {case_number}: {e}")
        return None

def main(waiver_event=None):
    config = load_config()
    sig_path = config.get("waiver.signature_image_path")
    output_dir = config.get("waiver.waiver_output_dir")
    bar = config.get("scraper.bar_number")

    csv_path = os.path.join(config["scraper.destination_folder"], f"{bar}_Cases.csv")
    template_path = os.path.join(os.path.expanduser("~"), "Desktop", f"Waiver {bar}.pdf")

    if not os.path.isfile(csv_path):
        print(f"[ERROR] Case CSV not found: {csv_path}")
        return
    if not os.path.isfile(template_path):
        print(f"[ERROR] Template PDF not found: {template_path}")
        return

    if waiver_event:
        print("\n*** Waiting for user to click 'Continue' in GUI before generating waivers... ***\n")
        waiver_event.wait()

    from PyPDF2 import PdfWriter

    writer = PdfWriter()
    with open(csv_path, "r", encoding="utf-7") as f:
        lines = f.readlines()[1:]  # Skip header
        for line in lines:
            fields = line.strip().split(",")
            if len(fields) >= 2:
                client_name, case_number = fields[0].strip(), fields[1].strip()
                page = create_waiver_page(template_path, sig_path, client_name, case_number)
                if page:
                    writer.add_page(page)

    date_str = datetime.date.today().strftime("%Y-%m-%d")
    outfile = os.path.join(output_dir, f"{date_str} {bar}.pdf")
    with open(outfile, "wb") as f_out:
        writer.write(f_out)
    print(f"\n✅ Waiver PDF created: {outfile}")

if __name__ == "__main__":
    main()
