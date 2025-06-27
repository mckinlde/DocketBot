# scripts/FavoriteButton/main.py

import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from lni import lni

# --- CONFIG ---
SCRIPT_PATH = os.path.abspath(__file__)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(SCRIPT_PATH), "..",".."))
CHROME_BINARY = os.path.join(BASE_DIR, "chrome-win64", "chrome.exe")
CHROMEDRIVER_BINARY = os.path.join(BASE_DIR, "chromedriver-win64", "chromedriver.exe")
PDF_TEMPLATE = os.path.join(BASE_DIR, "assets", "0000 New Matter Form.pdf")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

print(f"""🔎📂🕵️
SCRIPT_PATH = {SCRIPT_PATH}
BASE_DIR = {BASE_DIR}
CHROME_BINARY = {CHROME_BINARY}
CHROMEDRIVER_BINARY = {CHROMEDRIVER_BINARY}
PDF_TEMPLATE = {PDF_TEMPLATE}
OUTPUT_DIR = {OUTPUT_DIR}
""")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def create_driver():
    options = Options()
    options.binary_location = CHROME_BINARY
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    service = Service(CHROMEDRIVER_BINARY)
    return webdriver.Chrome(service=service, options=options)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <UBI>")
        sys.exit(1)

    ubi = sys.argv[1]
    print(f"🔍 Looking up UBI: {ubi}\n")

    driver = create_driver()
    try:
        contractors = lni(driver, ubi)

        print("📑 Final scraped contractors:")
        for contractor in contractors:
            try:
                for key, val in contractor.items():
                    print(f"  {key}: {val}")
                print()
            except Exception as e:
                print(e)
    finally:
        driver.quit()
