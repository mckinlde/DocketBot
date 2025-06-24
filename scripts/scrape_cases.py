import os
import csv
import sys
import time
import random
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import threading

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

"""
CONFIGURATION
-------------
This script loads the following values from `config.json`:

- "bar_number": (str) The attorney's WSBA bar number. 
                Used for logging into dw.courts.wa.gov and naming output files.

- "destination_folder": (str) Absolute or relative path to the folder 
                        where client case folders and CSVs will be created.

Example `config.json`:
{
    "bar_number": "12345",
    "destination_folder": "C:/Users/YourName/Desktop/Misdemeanor Clients"
}
"""

# === Load config ===
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Load config.json
config_path = resource_path("config.json")
with open(config_path, "r") as f:
    config = json.load(f)

BAR_NUMBER = config.get("bar_number")
DESTINATION_FOLDER = config.get("destination_folder")

# === Utility functions ===
def hide():
    time.sleep(random.randint(0, 2) + random.random())

def ensureFolder(path):
    os.makedirs(path, exist_ok=True)
    print(f"Ensured folder: {path}")

def normalize(s):
    """Remove whitespace, make uppercase, remove invisible characters."""
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
            next(reader, None)  # Skip header
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
        self.ready_event = threading.Event()

    def open_browser_and_wait(self):
        if not os.path.isfile(self.chrome_binary):
            print(f"Chrome binary not found at: {self.chrome_binary}")
            sys.exit(1)
        if not os.path.isfile(self.driver_binary):
            print(f"ChromeDriver binary not found at: {self.driver_binary}")
            sys.exit(1)

        chrome_options = Options()
        chrome_options.binary_location = self.chrome_binary
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        service = Service(self.driver_binary)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        print('Opening browser to login page...')
        self.driver.set_page_load_timeout(10)
        self.driver.get("https://dw.courts.wa.gov/index.cfm?fa=home.atty&terms=accept&flashform=0")

        print("\n*** Please complete the captcha in the browser window. ***")
        print("*** When done, click 'Continue' in the GUI. ***\n")

        self.ready_event.wait()

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

    if continue_event is None:
        scraper.open_browser_and_wait()
        scraper.scrape_cases()
    else:
        def open_browser_thread():
            scraper.open_browser_and_wait()
            scraper.scrape_cases()
        threading.Thread(target=open_browser_thread, daemon=True).start()
        continue_event.wait()
        scraper.ready_event.set()

if __name__ == "__main__":
    run_main()
