import os
import json
import time
import unicodedata
import re
from datetime import datetime
from io import BytesIO
from collections import defaultdict

from selenium import webdriver
from bs4 import BeautifulSoup
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image

CONFIG_PATH = os.path.join(os.environ["LOCALAPPDATA"], "DocketBot", "config.json")
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "Waiver PDF Form with bar number and signature.pdf")
CHROME_DRIVER_PATH = os.path.join(os.path.dirname(__file__), "..", "chromedriver-win64", "chromedriver.exe")

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def normalize_for_grouping(name):
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode()
    name = re.sub(r'\b(jr|sr|ii|iii|iv|v)\b\.?', '', name, flags=re.IGNORECASE)
    return re.sub(r'[^a-z]', '', name.lower())

def ensure_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created folder: {path}")

def create_overlay(name, case_str, year, signature_path):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    name_x, name_y = 60, 648
    case_x, case_y = 350, 643
    year_x, year_y = 356, 394
    sig_x, sig_y = 360, 428
    sig_width = 120

    # Add text fields
    can.setFont("Helvetica", 10)
    can.drawString(name_x, name_y, name)
    can.drawString(year_x, year_y, year)

    # Handle case wrapping
    case_nums = case_str.split(", ")
    current_line = ""
    lines = []
    max_width = 220
    for num in case_nums:
        test = current_line + (", " if current_line else "") + num
        if can.stringWidth(test, "Helvetica", 10) <= max_width:
            current_line = test
        else:
            lines.append(current_line)
            current_line = num
    if current_line:
        lines.append(current_line)
    font_size = 10 if len(lines) <= 2 else 9 if len(lines) <= 3 else 8
    for i, line in enumerate(lines):
        y_offset = case_y - i * (font_size + 2)
        can.setFont("Helvetica", font_size)
        can.drawString(case_x, y_offset, line)

    can.save()
    packet.seek(0)
    overlay = PdfReader(packet).pages[0]

    if os.path.exists(signature_path):
        sig_img = Image.open(signature_path)
        sig_buffer = BytesIO()
        sig_img.save(sig_buffer, format="PNG")
        sig_buffer.seek(0)

        sig_pdf = BytesIO()
        sig_can = canvas.Canvas(sig_pdf, pagesize=letter)
        sig_can.drawImage(sig_buffer, sig_x, sig_y, width=sig_width, preserveAspectRatio=True, mask='auto')
        sig_can.save()
        sig_pdf.seek(0)

        sig_overlay = PdfReader(sig_pdf).pages[0]
        PageMerge(overlay).add(sig_overlay).render()

    return overlay

def parse_case(soup):
    result = {}
    name_div = soup.find("div", class_="dw-icon-row")
    if name_div:
        result["Client Name"] = name_div.find_all("div")[-1].text.strip()
    try:
        result["Appointment Date"] = f"{soup.find('div', class_='dw-cal-result-month').text.strip()} {soup.find('div', class_='dw-cal-result-day').text.strip()}, {soup.find('div', class_='dw-cal-result-year').text.strip()}"
    except:
        result["Appointment Date"] = None

    for item in soup.find_all("div", class_="dw-cal-result-item"):
        label = item.find("div", class_="dw-cal-result-label").text.strip(": ")
        data = item.find("div", class_="dw-cal-result-data").text.strip()
        if label == "Case Number":
            data = data.split()[0]
        result[label] = data
    return result

def main(continue_event=None):
    config = load_config()
    sig_path = config["waiver.signature_image_path"]
    out_dir = config["waiver.waiver_output_dir"]

    ensure_folder(out_dir)

    driver = webdriver.Chrome(CHROME_DRIVER_PATH)
    driver.get("https://dw.courts.wa.gov/index.cfm?fa=home.atty&terms=accept&flashform=0")

    print("[INFO] Please complete captcha for waiver generation.")
    if continue_event:
        continue_event.wait()
        continue_event.clear()

    print("[INFO] Scraping waiver-eligible cases...")

    soup = BeautifulSoup(driver.page_source, "lxml")
    cases = []
    for case_soup in soup.find_all("div", class_="dw-search-result std-vertical-med-margin dw-cal-search-result"):
        data = parse_case(case_soup)
        if data.get("Court") == "SUNNYSIDE MUNICIPAL":
            cases.append(data)

    print(f"[INFO] {len(cases)} Sunnyside Municipal cases found.")

    grouped = defaultdict(list)
    for case in cases:
        name = case.get("Client Name", "Unknown")
        num = case.get("Case Number", "NoCaseNumber")
        key = normalize_for_grouping(name)
        grouped[key].append((name, num))

    writer = PdfWriter()
    year = datetime.now().strftime("%y")
    for group in grouped.values():
        name, _ = group[0]
        case_nums = ", ".join(sorted(set(n for _, n in group)))
        template = PdfReader(TEMPLATE_PATH).pages[0]
        overlay = create_overlay(name, case_nums, year, sig_path)
        PageMerge(template).add(overlay).render()
        writer.addpage(template)

    outfile = os.path.join(out_dir, f"{datetime.now().strftime('%Y-%m-%d')} Waivers.pdf")
    writer.write(outfile)
    print(f"\n✅ Waiver PDF generated: {outfile}")
    input("Press Enter to finish...")
    driver.quit()
