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
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

# --- CONFIG ---
SCRIPT_PATH = os.path.abspath(__file__)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(SCRIPT_PATH), ".."))
CHROME_BINARY = os.path.join(BASE_DIR, "chrome-win64", "chrome.exe")
CHROMEDRIVER_BINARY = os.path.join(BASE_DIR, "chromedriver-win64", "chromedriver.exe")
PDF_TEMPLATE = os.path.join(BASE_DIR, "assets", "000 New Matter Form.pdf")
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
def get_sos_info(driver, ubi):
    try:
        driver.get(f"https://ccfs.sos.wa.gov/#/BusinessSearch/UBI/{ubi}")
        print("SOS loaded. Press ENTER after navigating to the detail view.", end="")
        if not wait_for_continue():
            return {"status": "Not found"}

        # Add actual scraping logic here if needed
        return {"status": "Not implemented"}
    except Exception as e:
        print(f"SOS error: {e}")
        return {"status": "error"}

def get_lni_info(driver):
    try:
        driver.get("https://secure.lni.wa.gov/verify/")
        print("LNI loaded. Press ENTER after page settles.", end="")
        if not wait_for_continue():
            return {"status": "Not found"}

        return {"status": "Not implemented"}
    except Exception as e:
        print(f"LNI error: {e}")
        return {"status": "error"}

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
    print(f"Generating filled PDF at:\n{output_path}")
    reader = PdfReader(PDF_TEMPLATE)
    writer = PdfWriter()

    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawString(100, 700, f"SOS status: {sos.get('status', 'OK')}")
    can.drawString(100, 680, f"LNI status: {lni.get('status', 'OK')}")
    can.drawString(100, 660, f"DOR status: {dor.get('status', 'OK')}")
    can.save()

    packet.seek(0)
    overlay_pdf = PdfReader(packet)
    first_page = reader.pages[0]
    first_page.merge_page(overlay_pdf.pages[0])
    writer.add_page(first_page)

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
