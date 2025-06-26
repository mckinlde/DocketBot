# scripts/FavoriteButton/main.py

import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from lni import get_lni_contractors

def resource_path(relative_path):
    """Get absolute path to resource (for PyInstaller compatibility)."""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)

def create_driver():
    chrome_binary = resource_path(os.path.join("chrome-win64", "chrome.exe"))
    driver_binary = resource_path(os.path.join("chromedriver-win64", "chromedriver.exe"))

    options = Options()
    options.binary_location = chrome_binary
    options.add_experimental_option("detach", True)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(executable_path=driver_binary)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <UBI>")
        sys.exit(1)

    ubi = sys.argv[1]
    print(f"🔍 Looking up UBI: {ubi}\n")

    driver = create_driver()
    try:
        contractors = get_lni_contractors(driver, ubi)
    finally:
        driver.quit()
