# scripts/FavoriteButton/main.py

import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from lni import get_lni_contractors

def create_driver():
    options = Options()
    options.binary_location = "chrome-win64/chrome.exe"
    options.add_argument("--remote-debugging-port=0")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-device-discovery-notifications")

    service = Service("chromedriver-win64/chromedriver.exe")
    return webdriver.Chrome(service=service, options=options)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <UBI_NUMBER>")
        sys.exit(1)

    ubi = sys.argv[1]
    print(f"🔍 Looking up UBI: {ubi}\n")

    driver = create_driver()
    try:
        contractors = get_lni_contractors(driver, ubi)
        print("\n✅ LNI Contractor Info:")
        for c in contractors:
            for k, v in c.items():
                print(f"{k}: {v}")
            print("\n---\n")
    finally:
        driver.quit()
