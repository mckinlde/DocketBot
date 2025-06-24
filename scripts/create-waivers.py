import os
import json
from io import BytesIO
from datetime import datetime
from collections import defaultdict
import unicodedata
import re

from selenium import webdriver
from bs4 import BeautifulSoup
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

# === CONFIG ===
CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "waivers": {
        "output_dir": "C:/Users/stace/Desktop/1 STATE CRIMINAL/generated_waivers",
        "signature_path": "C:/Users/stace/Desktop/signature.png",
        "bar_number": "20789"
    },
    "scraper": {
        "output_dir": "C:/Users/stace/Desktop/1 STATE CRIMINAL/Cases"
    }
}

TEMPLATE_PDF_PATH = "C:/Users/stace/Desktop/Waiver PDF Form with bar number and signature.pdf"
CHROME_DRIVER_PATH = "C:/Users/stace/Documents/Python Scripts/chromedriver.exe"

# === UTILS ===
def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def normalize_for_grouping(name):
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode()
    name = re.sub(r'\b(jr|sr|ii|iii|iv|v)\b\.?', '', name, flags=re.IGNORECASE)
    return re.sub(r'[^a-z]', '', name.lower())

def parse_case(soup):
    result = {}
    name_div = soup.find('div', class_="dw-icon-row")
    if name_div:
        result["Client Name"] = name_div.find_all("div")[-1].text.strip()

    try:
        month = soup.find("div", class_="dw-cal-result-month").text.strip()
        day = soup.find("div", class_="dw-cal-result-day").text.strip()
        year = soup.find("div", class_="dw-cal-result-year").text.strip()
        result["Appointment Date"] = f"{month} {day}, {year}"
    except Exception:
        result["Appointment Date"] = None

    for item in soup.find_all("div", class_="dw-cal-result-item"):
        label = item.find("div", class_="dw-cal-result-label").text.strip(": ")
        data = item.find("div", class_="dw-cal-result-data").text.strip()
        if label == "Case Number":
            data = data.split(' ')[0]
        result[label] = data
    return result

# === PDF OVERLAY CREATION ===
def create_overlay(name, case_str, year, signature_path, bar_number):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Text fields
    can.setFont("Helvetica", 10)
    can.drawString(60, 648, name)       # Name
    can.drawString(356, 394, year)      # Year

    # Case numbers with wrapping
    case_nums = case_str.split(", ")
    current_line = ""
    lines = []
    for num in case_nums:
        test = (current_line + ", " if current_line else "") + num
        if can.stringWidth(test, "Helvetica", 10) <= 220:
            current_line = test
        else:
            lines.append(current_line)
            current_line = num
    if current_line:
        lines.append(current_line)

    font_size = 10 if len(lines) <= 2 else 9 if len(lines) <= 3 else 8
    for i, line in enumerate(lines):
        can.setFont("Helvetica", font_size)
        can.drawString(350, 643 - i * (font_size + 2), line)

    # Signature image
    if os.path.exists(signature_path):
        img = ImageReader(signature_path)
        can.drawImage(img, 100, 295, width=200, height=30, mask='auto')

    # Bar number
    can.setFont("Helvetica", 10)
    can.drawString(400, 245, f"WSBA# {bar_number}")

    can.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]

# === MAIN ===
def main():
    config = load_config()
    bar_number = config["waivers"]["bar_number"]
    signature_path = config["waivers"]["signature_path"]
    output_dir = config["waivers"]["output_dir"]

    # Default fallback: scrape_cases output dir
    if not output_dir or not os.path.exists(output_dir):
        output_dir = config["scraper"]["output_dir"]

    os.makedirs(output_dir, exist_ok=True)

    driver = webdriver.Chrome(CHROME_DRIVER_PATH)
    driver.set_page_load_timeout(10)
    driver.get("https://dw.courts.wa.gov/index.cfm?fa=home.atty&terms=accept&flashform=0")

    input("🔐 Solve captcha, then press Enter... ")
    driver.refresh()
    html = driver.page_source
    soup = BeautifulSoup(html, "lxml")

    case_soups = soup.find_all("div", class_="dw-search-result std-vertical-med-margin dw-cal-search-result")
    case_details = [parse_case(cs) for cs in case_soups if parse_case(cs).get("Court") == "SUNNYSIDE MUNICIPAL"]

    # Group by normalized name
    grouped = {}
    for case in case_details:
        raw = case.get("Client Name", "Unknown")
        key = normalize_for_grouping(raw)
        grouped.setdefault(key, {"name": raw, "case_numbers": []})["case_numbers"].append(case.get("Case Number", ""))

    # Create waiver PDF
    output_writer = PdfWriter()
    today = datetime.now()
    year_str = today.strftime("%y")
    date_str = today.strftime("%Y-%m-%d")

    for group in grouped.values():
        overlay = create_overlay(group["name"], ", ".join(group["case_numbers"]), year_str, signature_path, bar_number)
        template = PdfReader(TEMPLATE_PDF_PATH).pages[0]
        PageMerge(template).add(overlay).render()
        output_writer.addpage(template)

    out_path = os.path.join(output_dir, f"{date_str} Waivers.pdf")
    output_writer.write(out_path)
    print(f"✅ PDF saved to: {out_path}")
    input("Done. Press Enter to exit.")
    driver.quit()

if __name__ == "__main__":
    main()
