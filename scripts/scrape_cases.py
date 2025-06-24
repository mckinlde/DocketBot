# scripts/scrape_cases.py

import os
import csv
import sys
import time
import random
import json
import threading
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# === Config ===
def resource_path(path):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, path)

def load_config():
    config_path = os.path.join(os.environ["LOCALAPPDATA"], "DocketBot", "config.json")
    with open(config_path, "r") as f:
        return json.load(f)

config = load_config()
BAR_NUMBER = config.get("scraper.bar_number", "00000")
DESTINATION_FOLDER = config.get("scraper.destination_folder", os.path.expanduser("~/Desktop/00000 Misdemeanor Clients"))

# === Utility Functions ===
def hide():
    time.sleep(random.randint(0, 2) + random.random())

def ensureFolder(path):
    os.makedirs(path, exist_ok=True)
    print(f"📁 Ensured folder: {path}")

def normalize(s):
    return ''.join(s.split()).upper()

def parseCase(soup: BeautifulSoup):
    result = {}
    name_div = soup.find('div', class_="dw-icon-row")
    if name_div:
        name = name_div.find_all("div")[-1].text.strip()
        result["Client Name"] = name

    try:
        month = soup.find("div", class_="dw-cal-result-month").text.strip()
        day = soup.find("div", class_="dw-cal-result-day").text.strip()
        year = soup.find("div", class_="dw-cal-result-year").text.strip()
        result["Appointment Date"] = f"{month} {day}, {year}"
    except Exception:
        result["Appointment Date"] = ""

    items = soup.find_all("div", class_="dw-cal-result-item")
    for item in items:
        label = item.find("div", class_="dw-cal-result-label").text.strip(": ")
        data = item.find("div", class_="dw-cal-result-data").text.strip()
        if label == "Case Number":
            data = data.split(' ')[0]
        result[label] = data

    return result

def count_csv_rows(filepath):
    with open(filepath, 'r', newline='', encoding='utf-7') as file:
        reader = csv.reader(file)
        return sum(1 for _ in reader)

def write_cases_to_csv(bar_number, cases):
    ensureFolder(DESTINATION_FOLDER)
    csv_path = os.path.join(DESTINATION_FOLDER, f'{bar_number}_Cases.csv')

    seen = set()
    added = skipped = 0
    initial_length = 0
    if os.path.isfile(csv_path):
        initial_length = count_csv_rows(csv_path)
        with open(csv_path, 'r', newline='', encoding='utf-7') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    seen.add((normalize(row[0]), normalize(row[1])))
    else:
        print(f"{csv_path} doesn't exist, creating new file")

    file_mode = 'a' if os.path.isfile(csv_path) else 'w'
    with open(csv_path, file_mode, newline='', encoding='utf-7') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        if file_mode == 'w':
            writer.writerow(['Client Name', 'Case Number', 'Date', 'Case Count'])

        for case in cases:
            client_name = case.get('Client Name', '').strip()
            case_num = case.get('Case Number', '').strip()
            key = (normalize(client_name), normalize(case_num))

            if key not in seen:
                writer.writerow([client_name, case_num, "", ""])
                seen.add(key)
                added += 1
                print(f"✅ Added: {key}")
            else:
                skipped += 1
                print(f"⏩ Skipped duplicate: {key}")

    final_length = count_csv_rows(csv_path)
    print(f"""
CSV Write Summary:
  Initial length:     {initial_length}
  Final length:       {final_length}
  Cases added:        {added}
  Duplicates skipped: {skipped}
""")

class Scraper:
    def __init__(self):
        self.chrome_binary = resource_path(os.path.join("chrome-win64", "chrome.exe"))
        self.driver_binary = resource_path(os.path.join("chromedriver-win64", "chromedriver.exe"))
        self.driver = None

    def open_browser_and_wait(self, continue_event=None):
        print("[INFO] Launching browser before waiting on GUI...")
        print("🧠 Please complete the CAPTCHA in the browser.")
        print("⚠️ When ready, click \"Continue (after captcha)\" in the DocketBot GUI.\n")

        time.sleep(2)  # Let user read first

        chrome_options = Options()
        chrome_options.binary_location = self.chrome_binary
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--new-window")

        service = Service(self.driver_binary)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        self.driver.set_page_load_timeout(10)
        self.driver.get("https://dw.courts.wa.gov/index.cfm?fa=home.atty&terms=accept&flashform=0")
        time.sleep(2)

        if continue_event:
            continue_event.wait()

    def scrape_cases(self):
        hide()
        self.driver.refresh()
        time.sleep(2)

        html = self.driver.page_source
        soup = BeautifulSoup(html, "lxml")
        caseSoups = soup.find_all("div", class_="dw-search-result std-vertical-med-margin dw-cal-search-result")
        print(f'Found {len(caseSoups)} cases (before filtering)')

        caseDetails = []
        for case_soup in caseSoups:
            details = parseCase(case_soup)
            if details.get("Court") != "SUNNYSIDE MUNICIPAL":
                continue
            caseDetails.append(details)

        print(f'Filtered to {len(caseDetails)} Sunnyside cases.')

        ensureFolder(DESTINATION_FOLDER)

        for case in caseDetails:
            client = case.get('Client Name', 'Unknown')
            case_num = case.get('Case Number', 'NoCaseNumber')
            case_folder = f"{client}; {case_num}"
            case_folder_path = os.path.join(DESTINATION_FOLDER, case_folder)
            ensureFolder(case_folder_path)

        write_cases_to_csv(BAR_NUMBER, caseDetails)
        self.driver.quit()
        print("✅ Done!")

def run_main(continue_event=None):
    scraper = Scraper()

    def browser_then_scrape():
        scraper.open_browser_and_wait(continue_event)
        scraper.scrape_cases()

    threading.Thread(target=browser_then_scrape, daemon=True).start()

if __name__ == "__main__":
    run_main()
