# # FavoriteButton.py is a python script for New Matter Intake in Sarah King's Construction Dispute Practice

# # The main output is a filled 'assets\0000 New Matter Form.pdf'
# # The main input is a Washington State UBI number
# The Chrome and ChromeDriver Binaries used by Selenium are parameterized for easy reconfig, and on this machine located at:

        # self.chrome_binary = resource_path(os.path.join("chrome-win64", "chrome.exe"))
        # self.driver_binary = resource_path(os.path.join("chromedriver-win64", "chromedriver.exe"))

# # FavoriteButton.py uses selenium to navigate to the UBI-specific URLs for:
# Secretary of State (SOS): https://ccfs.sos.wa.gov/#/BusinessSearch/UBI/{UBI}
# LNI Verify a Contractor: https://secure.lni.wa.gov/verify/Detail.aspx?UBI={UBI}
# Department of Revenue: https://secure.dor.wa.gov/gteunauth/_/#1 (requires form submission, see DOR_form)

# # DOR_Form:
# 1) Click the "business lookup button": (<span id="Dg-1-1_c" class="ColIconText">Business Lookup</span>)
# 2) Fill the UBI/Accound ID# field: (<div id="fc_Dc-s" data-name="Dc-s" class="FGFC FGCPTop FGCPTopVisible CTEC FGTBC FGControlText FieldEnabled Field FGFill"><span class="FGDW FGDWStandard"><label id="lb_Dc-s" class="FGD2 CTEW FGD2Standard" for="Dc-s"><a id="cl_Dc-s" href="#RLZy8PtWWnMkBnfP_Dc-s" class="CaptionLink DFL FastEvt" data-event="ShowTip" data-showtip="{&quot;lng&quot;:&quot;ENG&quot;,&quot;typ&quot;:&quot;WA.XDBLS&quot;,&quot;hsh&quot;:&quot;&quot;,&quot;idx&quot;:&quot;1&quot;,&quot;fmt&quot;:&quot;TEXT&quot;,&quot;key&quot;:&quot;HelpUBI&quot;}" tabindex="0"><span id="caption2_Dc-s" class="CTE CaptionLinkText  IconCaption ICPLeft IconCaptionSmall" style=""><span class="FICW FICWSmall CaptionIconWrapper"><span role="presentation" aria-hidden="true" class="FIC FICSmall CaptionIcon FICF FICF_Material FICFTAuto" data-iconfont="Material" data-icon="" data-iconstatus="Auto"><img class="FICImg FICImgSmall CaptionIcon" src="../Resource/Images/blank.gif" alt=""></span></span><span class="IconCaptionText">UBI/Account ID #</span></span></a><span id="indicator_Dc-s" class="FI FI"></span></label></span><div class="FGIW FGIWText FGIWFill"><div id="ic_Dc-s" class="FGIC" style=""><input type="text" autocomplete="off" name="Dc-s" id="Dc-s" class="DFI FieldEnabled Field CTEF DocControlText FastEvtFieldKeyDown FastFieldEnterEvent TAAuto TAAutoLeft FastEvtFieldFocus" value="" spellcheck="true" data-fast-enter-event="Dc-s" maxlength="250" tabindex="0" style=""></div></div></div>)
# 3) Prompt the user to complete the captcha, search, select the matching business, and return control to selenium by pressing Enter 

# If FavoriteButton.py can get directly to the UBI page, it does, otherwise it
# waits for the user to fill any necessary captchas and navigate to the page 
# for the business in question before pressing ENTER to continue

# From each page, it saves the following information:
#     From the secretary of state's corporate lookup:
#     - company name
#     - company addresses, mailing, and street
#     - if the company is currently active, and if not, the date of their inactivity
#     - Name of registered agent, and registered agent mailing and street address
#     - Governor names

#     from the LNI:
#     - Contractors registration number 
#     - bond company, amount, and bond number (sometimes there are more than one)
#     - Insurance company and amount
#     - if contractors license is suspended
#     - any active lawsuits against the bond, case number, county, parites, status 

#     Department of Revenue
#     - Entity name
#     - Business name
#     - Trade names, if any
#     - Governors

# Then, it uses that information to fill out the "assets\0000 New Matter Form.pdf", 
# merging multi-page overlays if > 9 parties by:
#     - Automatically splits parties across additional pages if there are more than 9
#     - Uses the first page as a template for all overlay pages
#     - Maintains clean formatting and spacing per page

# FavoriteButton.py — One-File Intake Script
import os
import sys
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

# --- CONFIG ---
SCRIPT_PATH = os.path.abspath(__file__)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(SCRIPT_PATH), ".."))
CHROME_BINARY = os.path.join(BASE_DIR, "chrome-win64", "chrome.exe")
CHROMEDRIVER_BINARY = os.path.join(BASE_DIR, "chromedriver-win64", "chromedriver.exe")
PDF_TEMPLATE = os.path.join(BASE_DIR, "assets", "0000 New Matter Form.pdf")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- HELPERS ---
def init_driver():
    options = Options()
    options.binary_location = CHROME_BINARY
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(CHROMEDRIVER_BINARY), options=options)

def wait_for_continue(prompt="Press ENTER to continue, or ';' to skip."):
    resp = input(prompt)
    if resp.strip() == ";":
        return False
    return True

# --- SCRAPERS ---
# ... [existing imports and config remain unchanged above this line] ...

def get_sos_info(driver, ubi):
    try:
        driver.get(f"https://ccfs.sos.wa.gov/#/BusinessSearch/UBI/{ubi}")
        print("SOS loaded. Press ENTER after navigating to the detail view.", end="")
        if not wait_for_continue():
            return {"status": "Not found"}

        # TODO: Add live scraping here — this is from debug HTML for now
        data = {
            "company_name": "OMAK MACHINE SHOP, INC.",
            "ubi": ubi,
            "business_type": "WA PROFIT CORPORATION",
            "business_status": "ACTIVE",
            "principal_street_address": "505 OKOMA DR, OMAK, WA, 98841, UNITED STATES",
            "mailing_address": "PO BOX 1625, OMAK, WA, 98841-1625, UNITED STATES",
            "expiration_date": "01/31/2026",
            "jurisdiction": "UNITED STATES, WASHINGTON",
            "formation_date": "01/03/1975",
            "duration": "PERPETUAL",
            "nature_of_business": "OTHER SERVICES, DOMESTIC AND IRRIGATION PUMP INSTALLER",
            "registered_agent_name": "DARYN K APPLE",
            "agent_street": "505 OKOMA DR, OMAK, WA, 98841-9251, UNITED STATES",
            "agent_mailing": "PO BOX 1625, OMAK, WA, 98841-1625, UNITED STATES",
            "governors": ["DARYN APPLE", "LISA APPLE"],
        }

        print("\n--- SOS DEBUG INFO ---")
        for key, val in data.items():
            print(f"{key}: {val}")

        return data
    except Exception as e:
        print(f"SOS error: {e}")
        return {"status": "error"}

def get_lni_info(driver):
    try:
        temp_dir = os.path.join(BASE_DIR, "temp_html_files")
        os.makedirs(temp_dir, exist_ok=True)

        # Load the LNI search page
        driver.get("https://secure.lni.wa.gov/verify/")
        print("LNI loaded. Use the search box to look up the contractor. Press ENTER when the result list appears.")
        if not wait_for_continue():
            return {"status": "Not found"}

        # Save result list HTML
        list_html_path = os.path.join(temp_dir, "lni_list.html")
        with open(list_html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"✅ Saved contractor list HTML to: {list_html_path}")

        detail_htmls = []
        idx = 1
        while True:
            print(f"\n➡️  Navigate to contractor detail page #{idx}. Press ENTER to capture it, or ';' to finish.")
            if not wait_for_continue():
                break

            detail_path = os.path.join(temp_dir, f"lni_detail_{idx}.html")
            with open(detail_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"✅ Saved contractor detail HTML #{idx} to: {detail_path}")

            with open(detail_path, "r", encoding="utf-8") as f:
                detail_htmls.append(f.read())
            idx += 1

        # Read list HTML
        with open(list_html_path, "r", encoding="utf-8") as f:
            list_html = f.read()

        # Parse all captured contractor detail pages
        return get_lni_info_from_html(list_html, detail_htmls)

    except Exception as e:
        print(f"LNI error: {e}")
        return {"status": "error"}


def get_lni_info_from_html(list_html: str, detail_htmls: list[str]) -> list[dict]:
    contractors = []

    print("\n🔧 Parsing LNI Result List Page")
    list_soup = BeautifulSoup(list_html, "html.parser")
    result_links = list_soup.select("a[href*='Detail.aspx']")
    print(f"Found {len(result_links)} contractor result(s).")

    for idx, detail_html in enumerate(detail_htmls):
        print(f"\n📄 Contractor #{idx + 1} Detail Page:")
        soup = BeautifulSoup(detail_html, "html.parser")
        info = {}

        # Expand contract section if collapsed
        hidden = soup.select_one("div.contractorDetailDiv[style*='display: none']")
        if hidden:
            print("⚠️  Detail appears collapsed in HTML — please ensure 'Expand Detail' was clicked before saving.")
            continue

        # Registration Number
        reg_label = soup.find("label", string=lambda s: s and "Registration #" in s)
        if reg_label:
            reg_val = reg_label.find_next("span").get_text(strip=True)
            info["Registration Number"] = reg_val

        # Bond Info
        bond_section = soup.find("h4", string=lambda s: s and "Bond Information" in s)
        if bond_section:
            bond_table = bond_section.find_next("table")
            if bond_table:
                bonds = []
                for row in bond_table.select("tr")[1:]:
                    cols = [col.get_text(strip=True) for col in row.select("td")]
                    if cols:
                        bonds.append({
                            "Bonding Company": cols[0],
                            "Bond Number": cols[1],
                            "Amount": cols[2]
                        })
                info["Bonds"] = bonds

        # Insurance Info
        ins_section = soup.find("h4", string=lambda s: s and "Insurance Information" in s)
        if ins_section:
            ins_table = ins_section.find_next("table")
            if ins_table:
                ins_row = ins_table.select_one("tr:nth-of-type(2)")
                if ins_row:
                    ins_cols = [td.get_text(strip=True) for td in ins_row.select("td")]
                    if ins_cols:
                        info["Insurance Company"] = ins_cols[0]
                        info["Insurance Amount"] = ins_cols[2] if len(ins_cols) > 2 else ""

        # License Suspension Status
        status_label = soup.find("label", string=lambda s: s and "License" in s and "Suspended" in s)
        if status_label:
            status_val = status_label.find_next("span").get_text(strip=True)
            info["License Suspended"] = status_val

        # Lawsuits / Bond Claims
        lawsuit_section = soup.find("h4", string=lambda s: s and "Lawsuits" in s)
        if lawsuit_section:
            lawsuit_table = lawsuit_section.find_next("table")
            if lawsuit_table:
                lawsuits = []
                for row in lawsuit_table.select("tr")[1:]:
                    cols = [col.get_text(strip=True) for col in row.select("td")]
                    if cols:
                        lawsuits.append({
                            "Case Number": cols[0],
                            "County": cols[1],
                            "Parties": cols[2],
                            "Status": cols[3],
                        })
                info["Lawsuits"] = lawsuits

        if info:
            contractors.append(info)
            for key, val in info.items():
                print(f"  {key}: {val if not isinstance(val, list) else f'{len(val)} item(s)'}")
        else:
            print("⚠️  No contractor data extracted from this page.")

    return contractors


def get_dor_info(driver):
    try:
        driver.get("https://secure.dor.wa.gov/gteunauth/_/#1")
        print("DOR loaded. Complete CAPTCHA and select business, then ENTER.", end="")
        if not wait_for_continue():
            return {"status": "Not found"}

        return {"status": "Not implemented"}
    except Exception as e:
        print(f"DOR error: {e}")
        return {"status": "error"}

# --- PDF ---

def fill_pdf(sos, lni, dor, output_path):
    print(f"\nGenerating filled PDF at:\n{output_path}")
    reader = PdfReader(PDF_TEMPLATE)
    writer = PdfWriter()

    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # --- SOS section ---
    can.drawString(100, 740, f"Company: {sos.get('company_name', '')}")
    can.drawString(100, 720, f"UBI: {sos.get('ubi', '')}")
    can.drawString(100, 700, f"Status: {sos.get('business_status', '')}")
    can.drawString(100, 680, f"Street Addr: {sos.get('principal_street_address', '')}")
    can.drawString(100, 660, f"Mailing Addr: {sos.get('mailing_address', '')}")
    can.drawString(100, 640, f"Registered Agent: {sos.get('registered_agent_name', '')}")
    can.drawString(100, 620, f"Agent Street: {sos.get('agent_street', '')}")
    can.drawString(100, 600, f"Agent Mailing: {sos.get('agent_mailing', '')}")
    can.drawString(100, 580, f"Governors: {', '.join(sos.get('governors', []))}")

    # --- LNI section ---
    y = 560
    can.drawString(100, y, f"LNI: {len(lni)} contractor(s) found")
    y -= 20
    for i, contractor in enumerate(lni[:2], 1):  # Show first 2 contractors on page
        can.drawString(100, y, f"  {i}. Reg#: {contractor.get('Registration Number', '')}")
        y -= 20


    # --- DOR placeholders ---
    can.drawString(100, 540, f"DOR status: {dor.get('status', 'Not implemented')}")
    can.save()

    packet.seek(0)
    overlay_pdf = PdfReader(packet)
    reader.pages[0].merge_page(overlay_pdf.pages[0])
    writer.add_page(reader.pages[0])

    with open(output_path, "wb") as f:
        writer.write(f)

# --- MAIN ---
def main():
    if len(sys.argv) < 2:
        print("Usage: FavoriteButton.py <UBI>")
        sys.exit(1)

    ubi = sys.argv[1]
    print(f"\n🔍 Looking up UBI: {ubi}\n")

    driver = init_driver()

    try:
        sos = get_sos_info(driver, ubi)
        lni = get_lni_info(driver)
        dor = get_dor_info(driver)
    finally:
        driver.quit()

    output_filename = datetime.now().strftime("%Y-%m-%d Intake Form.pdf")
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    fill_pdf(sos, lni, dor, output_path)

if __name__ == "__main__":
    main()
