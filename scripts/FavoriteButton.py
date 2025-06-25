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

# # LNI contractor detail pages now load and extract structured data automatically. The script:
#     Clicks each contractor result element directly.
#     Waits for expected detail content.
#     Saves each page's HTML for debug.
#     Returns to the saved result list URL (instead of using a brittle back button).
# Extracts:
#     Registration number
#     Bond(s) (company, number, amount)
#     Insurance (company, amount)
#     License suspension status
#     Lawsuits (case number, county, parties, status)

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
import re

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


def get_lni_info(driver, ubi):
    from selenium.common.exceptions import (
        TimeoutException, StaleElementReferenceException, WebDriverException
    )

    try:
        driver.get("https://secure.lni.wa.gov/verify/")
        print("LNI loaded. Use the search box to look up the contractor. Press ENTER when the result list appears.")
        if not wait_for_continue():
            return {"status": "Not found"}

        temp_dir = os.path.join(BASE_DIR, "temp_html_files")
        os.makedirs(temp_dir, exist_ok=True)

        list_path = os.path.join(temp_dir, "lni_list.html")
        with open(list_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"✅ Saved contractor list HTML to: {list_path}")

        list_url = driver.current_url
        contractors = []

        result_divs = driver.find_elements(By.CSS_SELECTOR, "div.resultItem")
        if not result_divs:
            print("ℹ️  No LNI contractor results found.")
            return []

        for idx in range(len(result_divs)):
            try:
                print(f"\n➡️  Navigating to contractor detail page #{idx + 1}...")

                result_divs = driver.find_elements(By.CSS_SELECTOR, "div.resultItem")
                if idx >= len(result_divs):
                    print(f"⚠️  Skipping contractor #{idx + 1}: DOM changed or index out of bounds.")
                    break

                contractor_elem = result_divs[idx]
                driver.execute_script("arguments[0].scrollIntoView(true);", contractor_elem)
                contractor_elem.click()

                # Wait for a reliable anchor in the contractor detail page
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "layoutContainer"))
                )
                time.sleep(5)  # slight buffer to ensure render

                html = driver.page_source
                detail_path = os.path.join(temp_dir, f"lni_detail_{idx + 1}.html")
                with open(detail_path, "w", encoding="utf-8") as f:
                    print(f"🪶 Writing detail HTML to: {detail_path}")
                    f.write(html)
                print(f"✅ Saved contractor detail HTML #{idx + 1} to: {detail_path}")

                # Load the list HTML from disk
                with open(list_path, "r", encoding="utf-8") as list_file:
                    list_html = list_file.read()

                parsed_list = get_lni_info_from_html(list_html, [html])
                if parsed_list:
                    print("Extending contractor list")
                    contractors.extend(parsed_list)


            except TimeoutException:
                print(f"⚠️  Contractor detail page #{idx + 1} failed to load expected content.")
            except (StaleElementReferenceException, WebDriverException) as e:
                print(f"⚠️  Contractor #{idx + 1} navigation error: {e}")
            finally:
                # Return to results list page
                driver.get(list_url)
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.resultItem"))
                    )
                except TimeoutException:
                    print("⚠️  Could not return to result list from detail page.")
                    break

        return contractors

    except Exception as e:
        print(f"🚨 LNI navigation error: {e}")
        return {"status": "error"}


def get_lni_info_from_html(list_html: str, detail_htmls: list[str]) -> list[dict]:
    contractors = []
    print("\n🔧 Parsing LNI Result List Page")
    list_soup = BeautifulSoup(list_html, "html.parser")
    result_divs = list_soup.select("div.resultItem")
    print(f"Found {len(result_divs)} contractor result(s).")

    print("\n🔧 Parsing LNI Detail Pages")
    for idx, detail_html in enumerate(detail_htmls):
        soup = BeautifulSoup(detail_html, "html.parser")
        info = {}

        # Get contractor name for header
        name_tag = soup.select_one("div.hdrText")
        contractor_name = name_tag.get_text(strip=True) if name_tag else f"Contractor #{idx + 1}"
        print(f"\n📄 {contractor_name} Detail Page:")

        # Check if contractorDetailDiv is visible
        hidden = soup.select_one("div.contractorDetailDiv[style*='display: none']")
        if hidden:
            print("⚠️  Detail appears collapsed in HTML — skipping.")
            continue

        # Registration Number
        reg_td = soup.find("td", string=re.compile("Registration #", re.I))
        if reg_td:
            reg_val = reg_td.find_next("td").get_text(strip=True)
            info["Registration Number"] = reg_val

        # Bond Info
        bond_section = soup.find("h4", string=re.compile("Bond Information", re.I))
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

        if not reg_td:
            print("  ⚠️ Registration # not found")
        if not bond_section:
            print("  ⚠️ Bond Information not found")

        # Insurance Info
        ins_section = soup.find("h4", string=re.compile("Insurance Information", re.I))
        if ins_section:
            ins_table = ins_section.find_next("table")
            if ins_table:
                ins_row = ins_table.select_one("tr:nth-of-type(2)")
                if ins_row:
                    ins_cols = [td.get_text(strip=True) for td in ins_row.select("td")]
                    if ins_cols:
                        info["Insurance Company"] = ins_cols[0]
                        info["Insurance Amount"] = ins_cols[2] if len(ins_cols) > 2 else ""

        # License Suspension
        status_td = soup.find("td", string=re.compile("License.*Suspended", re.I))
        if status_td:
            status_val = status_td.find_next("td").get_text(strip=True)
            info["License Suspended"] = status_val

        # Lawsuits
        lawsuit_section = soup.find("h4", string=re.compile("Lawsuits", re.I))
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

def fill_pdf(sos, lni_contractors, dor, output_path):
    print(f"\n📝 Generating filled PDF at:\n{output_path}")
    reader = PdfReader(PDF_TEMPLATE)
    writer = PdfWriter()

    def draw_sos(can):
        can.drawString(100, 740, f"Company: {sos.get('company_name', '')}")
        can.drawString(100, 720, f"UBI: {sos.get('ubi', '')}")
        can.drawString(100, 700, f"Status: {sos.get('business_status', '')}")
        can.drawString(100, 680, f"Street Addr: {sos.get('principal_street_address', '')}")
        can.drawString(100, 660, f"Mailing Addr: {sos.get('mailing_address', '')}")
        can.drawString(100, 640, f"Registered Agent: {sos.get('registered_agent_name', '')}")
        can.drawString(100, 620, f"Agent Street: {sos.get('agent_street', '')}")
        can.drawString(100, 600, f"Agent Mailing: {sos.get('agent_mailing', '')}")
        can.drawString(100, 580, f"Governors: {', '.join(sos.get('governors', []))}")

    def draw_dor(can):
        can.drawString(100, 160, f"DOR status: {dor.get('status', 'Not implemented')}")

    # Create LNI pages with multiple contractors
    def create_lni_pages():
        pages = []
        max_lines_per_page = 30
        lines = []

        for idx, contractor in enumerate(lni_contractors):
            lines.append(f"Contractor #{idx + 1}")
            lines.append(f"Registration #: {contractor.get('Registration Number', 'N/A')}")

            for bond in contractor.get("Bonds", []):
                lines.append(f"  Bond - Company: {bond['Bonding Company']}, Number: {bond['Bond Number']}, Amount: {bond['Amount']}")

            lines.append(f"Insurance: {contractor.get('Insurance Company', 'N/A')} - {contractor.get('Insurance Amount', '')}")
            lines.append(f"License Suspended: {contractor.get('License Suspended', 'N/A')}")

            for lawsuit in contractor.get("Lawsuits", []):
                lines.append(f"  Lawsuit - Case: {lawsuit['Case Number']}, County: {lawsuit['County']}")
                lines.append(f"           Parties: {lawsuit['Parties']}, Status: {lawsuit['Status']}")

            lines.append("")  # spacer

        # Break into pages
        for i in range(0, len(lines), max_lines_per_page):
            page_lines = lines[i:i + max_lines_per_page]
            pages.append(page_lines)

        return pages

    # Render first page
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    draw_sos(can)
    draw_dor(can)
    can.drawString(100, 540, "LNI contractors (see next pages if more):")
    can.save()

    packet.seek(0)
    overlay_pdf = PdfReader(packet)
    first_page = reader.pages[0]
    first_page.merge_page(overlay_pdf.pages[0])
    writer.add_page(first_page)

    # Render LNI detail pages
    lni_pages = create_lni_pages()
    for page_lines in lni_pages:
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        y = 720
        for line in page_lines:
            can.drawString(80, y, line)
            y -= 20
        can.save()
        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        new_page = reader.pages[0]
        new_page.merge_page(overlay_pdf.pages[0])
        writer.add_page(new_page)

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
        lni = get_lni_info(driver, ubi)
        dor = get_dor_info(driver)
    finally:
        driver.quit()

    output_filename = datetime.now().strftime("%Y-%m-%d Intake Form.pdf")
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    fill_pdf(sos, lni, dor, output_path)

if __name__ == "__main__":
    main()
