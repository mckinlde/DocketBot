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
import copy
from io import BytesIO
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter

PARTIES_PER_PAGE = 9

# -- Configurable Chrome paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
def resource_path(rel): return os.path.join(BASE_DIR, rel)
CHROME_BINARY = resource_path("chrome-win64/chrome.exe")
CHROMEDRIVER_BINARY = resource_path("chromedriver-win64/chromedriver.exe")

# -- Setup Selenium

def setup_driver():
    options = Options()
    options.binary_location = CHROME_BINARY
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(service=Service(CHROMEDRIVER_BINARY), options=options)

# -- Overlay PDF Drawing

def overlay_text(fields, page_index=0):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    if page_index == 0:
        can.drawString(95, 668, fields.get("company_name", ""))
        can.drawString(95, 653, fields.get("care_of", ""))
        can.drawString(95, 638, fields.get("street_address", ""))
        can.drawString(95, 623, fields.get("city_state_zip", ""))
        can.drawString(95, 608, fields.get("email", ""))
        can.drawString(340, 608, fields.get("phone", ""))
        y = 593
        for line in fields.get("notes", []):
            can.drawString(95, y, line)
            y -= 12
    # Parties
    offset = page_index * PARTIES_PER_PAGE
    for i, p in enumerate(fields.get("parties", [])[offset:offset+PARTIES_PER_PAGE]):
        base_y = 480 - (i * 58)
        can.drawString(95, base_y, p["name"])
        can.drawString(95, base_y - 12, p["desc"])
        can.drawString(95, base_y - 24, p["assoc"])
    can.save()
    packet.seek(0)
    return packet

# -- PDF Fill Logic

def fill_pdf(sos, lni, dor, output_path):
    fields = {
        "company_name": sos.get("company_name") or dor.get("business_name", ""),
        "street_address": sos.get("street_address", ""),
        "city_state_zip": "",
        "care_of": sos.get("registered_agent", ""),
        "email": "", "phone": "",
        "notes": [],
        "parties": []
    }
    if sos.get("status"): fields["notes"].append(f"Status: {sos['status']}")
    if sos.get("inactive_date"): fields["notes"].append(f"Inactive since: {sos['inactive_date']}")
    if lni.get("license_status"): fields["notes"].append(f"LNI Status: {lni['license_status']}")

    fields["parties"].extend({"name": g, "desc": "Governor", "assoc": ""} for g in sos.get("governors", []) + dor.get("governors", []))
    for bond in lni.get("bonds", []):
        fields["parties"].append({"name": bond["bond_company"], "desc": f"${bond['bond_amount']} - Bond", "assoc": f"#{bond['bond_number']}"})
    for suit in lni.get("lawsuits", []):
        fields["parties"].append({"name": suit["parties"], "desc": f"Lawsuit in {suit['county']}", "assoc": f"{suit['case_number']} - {suit['status']}"})

    reader = PdfReader(resource_path("assets/000 New Matter Form.pdf"))
    writer = PdfWriter()
    total_pages = (len(fields["parties"]) + PARTIES_PER_PAGE - 1) // PARTIES_PER_PAGE or 1
    for i in range(total_pages):
        overlay = PdfReader(overlay_text(fields, i))
        page = copy.copy(reader.pages[0])
        page.merge_page(overlay.pages[0])
        writer.add_page(page)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"✅ PDF saved: {output_path}")

# -- Scraping Logic --

def get_sos_info(driver, ubi):
    url = f"https://ccfs.sos.wa.gov/#/BusinessSearch/UBI/{ubi}"
    driver.get(url)
    input("SOS loaded. Press ENTER after navigating to the detail view.")
    def get(label):
        try: return driver.find_element(By.XPATH, f"//h3[contains(text(), '{label}')]/following-sibling::p").text.strip()
        except: return None
    info = {
        "company_name": get("Business Name"),
        "status": get("Status"),
        "inactive_date": get("Inactive Date"),
        "street_address": get("Street Address"),
        "mailing_address": get("Mailing Address"),
        "registered_agent": get("Registered Agent"),
        "registered_agent_address": get("RA Address")
    }
    try:
        govs = driver.find_elements(By.XPATH, "//h3[contains(text(),'Governing Persons')]/following-sibling::ul/li")
        info["governors"] = [g.text.strip() for g in govs]
    except: info["governors"] = []
    return info

def get_lni_info(driver, ubi):
    url = f"https://secure.lni.wa.gov/verify/Detail.aspx?UBI={ubi}"
    driver.get(url)
    input("LNI loaded. Press ENTER after page settles.")
    def safe(id):
        try: return driver.find_element(By.ID, id).text.strip()
        except: return None
    info = {
        "contractor_registration_number": safe("MainContent_lblContrRegNum"),
        "license_status": safe("MainContent_lblContrStatus"),
        "insurance_company": safe("MainContent_lblInsCarrier"),
        "insurance_amount": safe("MainContent_lblInsAmount")
    }
    info["bonds"] = []
    info["lawsuits"] = []
    try:
        for row in driver.find_elements(By.XPATH, "//table[@id='MainContent_gvBond']/tbody/tr")[1:]:
            tds = row.find_elements(By.TAG_NAME, "td")
            info["bonds"].append({"bond_company": tds[0].text, "bond_amount": tds[1].text, "bond_number": tds[2].text})
    except: pass
    try:
        for row in driver.find_elements(By.XPATH, "//table[@id='MainContent_gvLawsuit']/tbody/tr")[1:]:
            tds = row.find_elements(By.TAG_NAME, "td")
            info["lawsuits"].append({"case_number": tds[0].text, "county": tds[1].text, "parties": tds[2].text, "status": tds[3].text})
    except: pass
    return info

def get_dor_info(driver, ubi):
    driver.get("https://secure.dor.wa.gov/gteunauth/_/#1")
    input("DOR loaded. Complete CAPTCHA and select business, then ENTER.")
    def safe(id):
        try: return driver.find_element(By.ID, id).text.strip()
        except: return None
    info = {
        "entity_name": safe("ctl00_ContentPlaceHolder1_lblEntityName"),
        "business_name": safe("ctl00_ContentPlaceHolder1_lblBusinessName")
    }
    try:
        info["trade_names"] = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_lblTradeNames").text.split("\n")
    except: info["trade_names"] = []
    try:
        rows = driver.find_elements(By.XPATH, "//table[@id='ctl00_ContentPlaceHolder1_gvPrincipals']/tbody/tr")[1:]
        info["governors"] = [row.text.strip() for row in rows if row.text.strip()]
    except: info["governors"] = []
    return info

# -- Main Entry Point --

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python FavoriteButton.py <UBI_NUMBER>")
        sys.exit(1)
    ubi = sys.argv[1].strip()
    driver = setup_driver()
    sos = get_sos_info(driver, ubi)
    lni = get_lni_info(driver, ubi)
    dor = get_dor_info(driver, ubi)
    driver.quit()
    today = datetime.today().strftime("%Y-%m-%d")
    output_file = resource_path(f"output/{today}_{ubi}_filled.pdf")
    fill_pdf(sos, lni, dor, output_file)
