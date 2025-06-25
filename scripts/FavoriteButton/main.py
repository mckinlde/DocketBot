# main.py

# main.py creates the driver, accepts a UBI number as input, and imports and calls
# various utility functions to implement the FavoriteButton spec.

# main.py does not do any of its own webscraping or pdf writing, and currently only
# performs calls for LNI, from which it gets scraped/parsed data to output to the console.

# FavouriteButton Spec:
# # FavoriteButton is a python program for New Matter Intake in Sarah King's Construction Dispute Practice
# # The main output is a filled 'assets\0000 New Matter Form.pdf'
# # The main input is a Washington State UBI number
# The Chrome and ChromeDriver Binaries used by Selenium are parameterized for easy reconfig, and on this machine located at:
        # self.chrome_binary = resource_path(os.path.join("chrome-win64", "chrome.exe"))
        # self.driver_binary = resource_path(os.path.join("chromedriver-win64", "chromedriver.exe"))
# # FavoriteButton uses selenium to navigate to the UBI-specific URLs for:
# Secretary of State (SOS): https://ccfs.sos.wa.gov/#/BusinessSearch/UBI/{UBI}
# LNI Verify a Contractor: https://secure.lni.wa.gov/verify/Detail.aspx?UBI={UBI}
# Department of Revenue: https://secure.dor.wa.gov/gteunauth/_/#1 (requires form submission, see DOR_form)

# If FavoriteButton can get directly to the UBI page, it does, otherwise it
# waits for the user to fill any necessary captchas and navigate to the page 
# for the business in question before pressing ENTER to continue

# From each page, it saves information, and then calls fill_pdf.py to write it to the PDF form.

import os
import sys
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from lni_scraper import get_lni_info
# from sos_scraper import get_sos_info  # To be implemented
# from dor_scraper import get_dor_info  # To be implemented
# from fill_pdf import fill_pdf         # To be implemented

# CONFIG
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CHROME_BINARY = os.path.join(BASE_DIR, "chrome-win64", "chrome.exe")
CHROMEDRIVER_BINARY = os.path.join(BASE_DIR, "chromedriver-win64", "chromedriver.exe")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# UTILS
def init_driver():
    options = Options()
    options.binary_location = CHROME_BINARY
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(CHROMEDRIVER_BINARY), options=options)


# MAIN

def main():
    if len(sys.argv) < 2:
        print("Usage: main.py <UBI>")
        sys.exit(1)

    ubi = sys.argv[1]
    print(f"\n🔍 Looking up UBI: {ubi}\n")

    driver = init_driver()

    try:
        # sos_info = get_sos_info(driver, ubi)
        lni_info = get_lni_info(driver, ubi)
        # dor_info = get_dor_info(driver, ubi)

        print("\n✅ LNI Contractor Info:")
        for contractor in lni_info:
            print("\n--- Contractor ---")
            for key, val in contractor.items():
                if isinstance(val, list):
                    print(f"{key}:")
                    for item in val:
                        print(f"  • {item}")
                else:
                    print(f"{key}: {val}")

        # output_filename = datetime.now().strftime("%Y-%m-%d Intake Form.pdf")
        # output_path = os.path.join(OUTPUT_DIR, output_filename)
        # fill_pdf(sos_info, lni_info, dor_info, output_path)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
