import os
import json
import time
import csv
import unicodedata
import re
from datetime import datetime
from selenium import webdriver
from bs4 import BeautifulSoup

CONFIG_PATH = os.path.join(os.environ["LOCALAPPDATA"], "DocketBot", "config.json")

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

CHROME_DRIVER_PATH = os.path.join(os.path.dirname(__file__), "..", "chromedriver-win64", "chromedriver.exe")

def normalize_for_grouping(name):
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode()
    name = re.sub(r'\b(jr|sr|ii|iii|iv|v)\b\.?', '', name, flags=re.IGNORECASE)
    return re.sub(r'[^a-z]', '', name.lower())

def ensure_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created folder: {path}")

def run_main(continue_event=None):
    config = load_config()
    bar_number = config["scraper.bar_number"]
    dest_folder = config["scraper.destination_folder"]

    ensure_folder(dest_folder)

    driver = webdriver.Chrome(CHROME_DRIVER_PATH)
    driver.set_page_load_timeout(10)
    driver.get("https://dw.courts.wa.gov/index.cfm?fa=home.atty&terms=accept&flashform=0")

    print("\n[INFO] Please complete the captcha in the browser window.")
    if continue_event:
        continue_event.wait()
        continue_event.clear()

    print("\n[INFO] Scraping started...")

    soup = BeautifulSoup(driver.page_source, "lxml")
    cases = soup.find_all("div", class_="dw-search-result std-vertical-med-margin dw-cal-search-result")

    output_csv = os.path.join(dest_folder, f"{datetime.now().strftime('%Y-%m-%d')}_cases.csv")
    with open(output_csv, "w", newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Client Name", "Case Number", "Court"])

        for case_soup in cases:
            name_div = case_soup.find('div', class_="dw-icon-row")
            name = name_div.find_all("div")[-1].text.strip() if name_div else "Unknown"

            fields = case_soup.find_all("div", class_="dw-cal-result-item")
            data = {item.find("div", class_="dw-cal-result-label").text.strip(": "):
                        item.find("div", class_="dw-cal-result-data").text.strip()
                    for item in fields}
            case_num = data.get("Case Number", "").split()[0]
            court = data.get("Court", "")

            writer.writerow([name, case_num, court])
            print(f"Saved: {name}, {case_num}, {court}")

    print(f"\n✅ Done! Cases saved to: {output_csv}")
    input("Press Enter to close...")
    driver.quit()
