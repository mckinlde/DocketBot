import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from LNI import navigate_lni, get_lni_contractors

# --- CONFIG ---
SCRIPT_PATH = os.path.abspath(__file__)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHROME_BINARY = os.path.join(BASE_DIR, "chrome-win64", "chrome.exe")
CHROMEDRIVER_BINARY = os.path.join(BASE_DIR, "chromedriver-win64", "chromedriver.exe")

def init_driver():
    options = Options()
    options.binary_location = CHROME_BINARY
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(CHROMEDRIVER_BINARY), options=options)

def main():
    if len(sys.argv) < 2:
        print("Usage: main.py <UBI>")
        sys.exit(1)

    ubi = sys.argv[1]
    print(f"\n🔍 Looking up UBI: {ubi}\n")
    driver = init_driver()

    try:
        if not navigate_lni(driver, ubi):
            print("❌ LNI navigation failed. Please check the UBI and try again.")
            return

        contractors = get_lni_contractors(driver)
        print("\n✅ LNI Contractor Info:\n")
        for i, contractor in enumerate(contractors):
            print(f"--- Contractor #{i+1} ---")
            for k, v in contractor.items():
                print(f"{k}: {v}")
            print()

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
