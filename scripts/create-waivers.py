from selenium import webdriver
import time
import random
from bs4 import BeautifulSoup
import os
from io import BytesIO
from datetime import datetime
from collections import defaultdict
import unicodedata
import re
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# --- CONFIG ---
CHROME_DRIVER_PATH = "C:/Users/stace/Documents/Python Scripts/chromedriver.exe"
BASE_PATH = 'C:\\Users\\stace\\Desktop\\1 STATE CRIMINAL\\Cases'
SHARED_ROOT = 'C:\\Users\\stace\\Desktop\\SSMC Discovery and Offers'
WAIVER_PATHS = {
    "doug": "C:/Users/stace/Desktop/Waiver DEM 20806 PDF.pdf",
    "stacey": "C:/Users/stace/Desktop/Waiver SMM 20789 PDF.pdf"
}
OUTPUT_DIR = 'C:/Users/stace/Desktop/1 STATE CRIMINAL/generated_waivers/'

# --- UTILS ---
def hide():
    time.sleep(random.randint(0, 2) + random.random())

def normalize_for_grouping(name):
    """Lowercase, remove suffixes, accents, and non-a-z chars for grouping."""
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode()
    name = re.sub(r'\b(jr|sr|ii|iii|iv|v)\b\.?', '', name, flags=re.IGNORECASE)
    return re.sub(r'[^a-z]', '', name.lower())

def ensureFolder(folder_name, base_path):
    new_directory = os.path.join(base_path, folder_name)
    if not os.path.exists(new_directory):
        os.makedirs(new_directory)
        print('Created folder: ' + new_directory)

def parseCase(soup: BeautifulSoup):
    result = {}
    name_div = soup.find('div', class_="dw-icon-row")
    if name_div:
        name = name_div.find_all("div")[-1].text.strip()
        result["Client Name"] = name

    try:
        month = soup.find("div", class_="dw-cal-result-month").text.strip()
        day = soup.find("div", class_="dw-cal-result-day").text.strip()
        year = soup.find("div", class_="dw-cal-result-year").text.strip()
        result["Appointment Date"] = f"{month} {day}, {year}"
    except Exception:
        result["Appointment Date"] = None

    items = soup.find_all("div", class_="dw-cal-result-item")
    for item in items:
        label = item.find("div", class_="dw-cal-result-label").text.strip(": ")
        data = item.find("div", class_="dw-cal-result-data").text.strip()
        if label == "Case Number":
            data = data.split(' ')[0]
        result[label] = data

    return result

# === START ===

driver = webdriver.Chrome(CHROME_DRIVER_PATH)
driver.set_page_load_timeout(10)

hide()
driver.get("https://dw.courts.wa.gov/index.cfm?fa=home.atty&terms=accept&flashform=0")
time.sleep(2)
captcha_filled = input('Are we filling for Doug or Stacey? Complete captcha, then type d/s and press enter: ').lower()
driver.refresh()

if captcha_filled == 'd':
    selected_attorney = 'doug'
elif captcha_filled == 's':
    selected_attorney = 'stacey'
else:
    print('❌ Error: Please input "d" or "s".')
    driver.quit()
    exit(1)

html = driver.page_source
soup = BeautifulSoup(html, "lxml")

caseSoups = soup.find_all("div", class_="dw-search-result std-vertical-med-margin dw-cal-search-result")
print(f"Cases found online, before filtering for Sunnyside: {len(caseSoups)}")

caseDetails = []
for case_soup in caseSoups:
    details = parseCase(case_soup)
    if details.get("Court") != "SUNNYSIDE MUNICIPAL":
        continue
    caseDetails.append(details)

print(f"After filtering for Sunnyside: {len(caseDetails)}")

# Folder setup
ensureFolder('Cases', BASE_PATH)
ensureFolder(f'Clients {selected_attorney.title()} McKinley', SHARED_ROOT)

attorney_root = os.path.join(BASE_PATH, selected_attorney.title())
ensureFolder(selected_attorney.title(), BASE_PATH)

for case in caseDetails:
    client = case.get('Client Name', 'Unknown')
    case_num = case.get('Case Number', 'NoCaseNumber')
    case_folder = f"{client}; {case_num}"
    ensureFolder(case_folder, attorney_root)

shared_attorney_root = os.path.join(SHARED_ROOT, f"Clients {selected_attorney.title()} McKinley")
for case in caseDetails:
    client = case.get('Client Name', 'Unknown')
    case_num = case.get('Case Number', 'NoCaseNumber')
    case_folder = f"{client}; {case_num}"
    ensureFolder(case_folder, shared_attorney_root)

# === PDF FILLING ===

def create_overlay(name, case_num, year):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Field positions
    name_x, name_y = 60, 648
    cases_x, cases_y = 350, 643
    year_x, year_y = 356, 394
    max_width = 220  # max width for case numbers field

    # Draw name and year (fixed size)
    can.setFont("Helvetica", 10)
    can.drawString(name_x, name_y, name)
    can.drawString(year_x, year_y, year)

    # Try drawing case numbers with wrapping
    case_nums = case_num.split(", ")
    current_line = ""
    lines = []
    for num in case_nums:
        test_line = current_line + (", " if current_line else "") + num
        if can.stringWidth(test_line, "Helvetica", 10) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = num
    if current_line:
        lines.append(current_line)

    # Reduce font size if too many lines
    font_size = 10
    if len(lines) > 2:
        font_size = 9 if len(lines) <= 3 else 8

    # Draw the wrapped lines
    for i, line in enumerate(lines):
        y_offset = cases_y - (i * (font_size + 2))  # adjust line spacing
        can.setFont("Helvetica", font_size)
        can.drawString(cases_x, y_offset, line)

    can.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]


today = datetime.now()
date_string = today.strftime('%Y-%m-%d')
year_string = today.strftime('%y')  # two-digit year

os.makedirs(OUTPUT_DIR, exist_ok=True)
template_path = WAIVER_PATHS[selected_attorney]
output_writer = PdfWriter()

# Group by normalized name, preserve first actual name seen
case_groups = {}

for case in caseDetails:
    raw_name = case.get('Client Name', 'Unknown')
    case_num = case.get('Case Number', 'NoCaseNumber')
    norm_key = normalize_for_grouping(raw_name)

    if norm_key not in case_groups:
        case_groups[norm_key] = {
            "name": raw_name,
            "case_numbers": []
        }

    case_groups[norm_key]["case_numbers"].append(case_num)

# Generate one page per grouped client
for group in case_groups.values():
    name = group["name"]
    case_nums = group["case_numbers"]
    all_cases = ", ".join(case_nums)

    template_pdf = PdfReader(template_path)
    template_page = template_pdf.pages[0]

    overlay = create_overlay(name, all_cases, year_string)
    merged = PageMerge(template_page)
    merged.add(overlay)
    merged.render()

    output_writer.addpage(template_page)

# Save final PDF
final_path = os.path.join(OUTPUT_DIR, f"{date_string} {selected_attorney.title()}.pdf")
output_writer.write(final_path)

print(f"\n✅ PDF generated: {final_path}")
input('Done! Press enter to close the robot.')
driver.quit()
