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
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import threading

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
DESTINATION_FOLDER = config.get("destination_folder")  # e.g. "Doug Misdemeanor Clients"

# === Utility functions ===
def hide():
    time.sleep(random.randint(0, 2) + random.random())

def ensureFolder(path):
    os.makedirs(path, exist_ok=True)
    print(f"Ensured folder: {path}")

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

def write_cases_to_csv(bar_number, cases):
    ensureFolder(DESTINATION_FOLDER)

    csv_path = os.path.join(DESTINATION_FOLDER, f'{bar_number}_Cases.csv')
    seen = set()

    if os.path.isfile(csv_path):
        print(f'{csv_path} exists')
        with open(csv_path, 'r', newline='') as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 2:
                    seen.add((row[0].strip(), row[1].strip()))
    else:
        print(f"{csv_path} doesn't exist, creating new file")

    file_mode = 'a' if os.path.isfile(csv_path) else 'w'
    with open(csv_path, file_mode, newline='') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        if file_mode == 'w':
            writer.writerow(['Client Name', 'Case Number', 'Date', 'Case Count'])

        for case in cases:
            client_name = case.get('Client Name', '').strip()
            case_num = case.get('Case Number', '').strip()
            key = (client_name, case_num)
            if key not in seen:
                writer.writerow([client_name, case_num, "", ""])
                seen.add(key)
                print(f"Case {key} added to CSV")
            else:
                print(f"Case {key} already in CSV")

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
                
        # Autofill bar number
        try:
            bar_input = self.driver.find_element(By.ID, "Bar_Nbr")
            bar_input.clear()
            bar_input.send_keys(BAR_NUMBER)
            print(f"Set Bar Number to {BAR_NUMBER}")
        except Exception as e:
            print("⚠️ Failed to autofill bar number:", e)

        # Select 90 from dropdown menu using JS and interaction
        try:
            dropdown_anchor = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "mdc-select__anchor"))
            )
            dropdown_anchor.click()

            option_90 = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'li.mdc-list-item[data-value="90"]'))
            )

            ActionChains(self.driver).move_to_element(option_90).click().perform()
            print("Set number of days to 90")
        except Exception as e:
            print("⚠️ Failed to set number of days to 90:", e)

        print("\n*** Please complete the captcha or login in the opened browser window. ***")
        print("*** When done, click the 'Continue' button in the GUI to proceed. ***\n")

        # Wait until the GUI signals to continue
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
            print(details)
            caseDetails.append(details)

        # Ensure the root folder is present
        ensureFolder(DESTINATION_FOLDER)

        # Create case folders inside the root
        for case in caseDetails:
            client = case.get('Client Name', 'Unknown')
            case_num = case.get('Case Number', 'NoCaseNumber')
            case_folder = f"{client}; {case_num}"
            case_folder_path = os.path.join(DESTINATION_FOLDER, case_folder)
            ensureFolder(case_folder_path)

        # Write to CSV inside the same root
        write_cases_to_csv(BAR_NUMBER, caseDetails)

        self.driver.quit()
        print("Done!")

def run_main(continue_event=None):
    scraper = Scraper()

    if continue_event is None:
        # No event means just run all normally (CLI mode)
        scraper.open_browser_and_wait()
        scraper.scrape_cases()
    else:
        # GUI mode: open browser, then wait for signal to continue
        # Start browser in separate thread to avoid blocking GUI
        def open_browser_thread():
            scraper.open_browser_and_wait()
            scraper.scrape_cases()
        threading.Thread(target=open_browser_thread, daemon=True).start()

        # Wait for GUI signal
        continue_event.wait()
        scraper.ready_event.set()

if __name__ == "__main__":
    run_main()
