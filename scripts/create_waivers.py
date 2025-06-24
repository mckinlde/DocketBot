import os
import sys
import time
import random
import re
import unicodedata
import json
from io import BytesIO
from datetime import datetime
from collections import defaultdict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

CHROME_PATH = "chrome-win64/chrome.exe"
CHROMEDRIVER_PATH = "chromedriver-win64/chromedriver.exe"
MAX_CASE_WIDTH = 220

def resource_path(path):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, path)

def load_config():
    path = os.path.join(os.environ["LOCALAPPDATA"], "DocketBot", "config.json")
    with open(path, "r") as f:
        return json.load(f)

def hide():
    time.sleep(random.randint(0, 2) + random.random())

def normalize_for_grouping(name):
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode()
    name = re.sub(r'\b(jr|sr|ii|iii|iv|v)\b\.?', '', name, flags=re.IGNORECASE)
    return re.sub(r'[^a-z]', '', name.lower())

def create_overlay(name, case_num, year, sig_path=None, bar_number="00000"):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Top fields
    name_x, name_y = 60, 648
    cases_x, cases_y = 350, 643
    year_x, year_y = 356, 394

    # Signature + bar fields
    sig_x, sig_y = 72, 115         # aligned behind "Signature:" line
    bar_x, bar_y = 390, 102        # aligned next to "WSBA#" field

    # Draw name and year
    can.setFont("Helvetica", 10)
    can.drawString(name_x, name_y, name)
    can.drawString(year_x, year_y, year)

    # Wrap case numbers
    case_nums = case_num.split(", ")
    current_line = ""
    lines = []
    for num in case_nums:
        test_line = current_line + (", " if current_line else "") + num
        if can.stringWidth(test_line, "Helvetica", 10) <= MAX_CASE_WIDTH:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = num
    if current_line:
        lines.append(current_line)

    font_size = 10
    if len(lines) > 2:
        font_size = 9 if len(lines) <= 3 else 8

    for i, line in enumerate(lines):
        y_offset = cases_y - (i * (font_size + 2))
        can.setFont("Helvetica", font_size)
        can.drawString(cases_x, y_offset, line)

    # Signature image
    if sig_path and os.path.exists(sig_path):
        try:
            from reportlab.lib.utils import ImageReader
            img = ImageReader(sig_path)
            can.drawImage(img, sig_x, sig_y, width=180, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"[ERROR] Failed to add signature image: {e}")

    # Bar number
    can.setFont("Helvetica", 10)
    can.drawString(bar_x, bar_y, bar_number)

    can.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]

def parse_case(soup: BeautifulSoup):
    result = {}
    name_div = soup.find('div', class_="dw-icon-row")
    if name_div:
        name = name_div.find_all("div")[-1].text.strip()
        result["Client Name"] = name

    items = soup.find_all("div", class_="dw-cal-result-item")
    for item in items:
        label = item.find("div", class_="dw-cal-result-label").text.strip(": ")
        data = item.find("div", class_="dw-cal-result-data").text.strip()
        if label == "Case Number":
            data = data.split(' ')[0]
        result[label] = data

    result["Court"] = result.get("Court", "")
    return result


def run_browser_and_scrape(event=None):
    print("[INFO] Launching browser before waiting on GUI...")
    print("🧠 Please complete the CAPTCHA in the browser.")
    print("⚠️ When ready, click \"Continue (after captcha)\" in the DocketBot GUI.\n")
    
    time.sleep(2)  # Let the user read

    chrome_options = Options()
    chrome_options.binary_location = resource_path(CHROME_PATH)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--new-window")

    driver = webdriver.Chrome(service=Service(resource_path(CHROMEDRIVER_PATH)), options=chrome_options)
    driver.set_page_load_timeout(10)

    hide()
    driver.get("https://dw.courts.wa.gov/index.cfm?fa=home.atty&terms=accept&flashform=0")
    time.sleep(2)

    if event:
        event.wait()

    driver.refresh()
    time.sleep(3)

    html = driver.page_source
    soup = BeautifulSoup(html, "lxml")

    case_soups = soup.find_all("div", class_="dw-search-result std-vertical-med-margin dw-cal-search-result")
    print(f"Found {len(case_soups)} cases (before filtering)...")

    case_details = []
    for case_soup in case_soups:
        parsed = parse_case(case_soup)
        if parsed.get("Court", "").strip().upper() != "SUNNYSIDE MUNICIPAL":
            continue
        case_details.append(parsed)

    print(f"🧾 Filtered to {len(case_details)} Sunnyside cases.")
    driver.quit()
    return case_details


def main(event=None):
    config = load_config()
    bar_number = config.get("scraper.bar_number", "00000")
    sig_path = config.get("waiver.signature_image_path")
    output_dir = config.get("waiver.waiver_output_dir")
    template_path = resource_path("assets/waiver_template.pdf")

    if not os.path.exists(template_path):
        print(f"[ERROR] Template not found: {template_path}")
        return

    today = datetime.now()
    date_string = today.strftime('%Y-%m-%d')
    year_string = today.strftime('%y')
    out_path = os.path.join(output_dir, f"{date_string} {bar_number}.pdf")
    os.makedirs(output_dir, exist_ok=True)

    case_details = run_browser_and_scrape(event)
    grouped = {}

    for case in case_details:
        raw_name = case.get("Client Name", "Unknown")
        case_num = case.get("Case Number", "NoCaseNumber")
        norm_key = normalize_for_grouping(raw_name)
        if norm_key not in grouped:
            grouped[norm_key] = {"name": raw_name, "case_numbers": []}
        grouped[norm_key]["case_numbers"].append(case_num)

    output_writer = PdfWriter()
    for group in grouped.values():
        name = group["name"]
        cases = ", ".join(group["case_numbers"])
        base_pdf = PdfReader(template_path)
        page = base_pdf.pages[0]
        overlay = create_overlay(name, cases, year_string)
        page.merge_page(overlay)
        output_writer.add_page(page)

    with open(out_path, "wb") as f:
        output_writer.write(f)
    print(f"\n✅ Waiver PDF generated: {out_path}")

if __name__ == "__main__":
    main()
