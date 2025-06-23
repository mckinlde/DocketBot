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

# === Load config ===
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Load config.json
config_path = resource_path("config.json")
with open(config_path, "r") as f:
    config = json.load(f)

# Re-assign BAR_NUMBER in case config changed at runtime
BAR_NUMBER = config.get("bar_number")
BASE_PATH = config.get("base_path")
SHARED_ROOT = config.get("shared_root")

# === Utility functions ===
def hide():
    time.sleep(random.randint(0, 2) + random.random())

def ensureFolder(folder_name, root_path):
    path = os.path.join(root_path, folder_name)
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
    person_dir = os.path.join(BASE_PATH, bar_number)
    os.makedirs(person_dir, exist_ok=True)

    csv_path = os.path.join(person_dir, f'{bar_number}_Cases.csv')
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

def run_main():
    # === Launch Chrome Driver ===
    chrome_binary = resource_path(os.path.join("chrome-win64", "chrome.exe"))
    driver_binary = resource_path(os.path.join("chromedriver-win64", "chromedriver.exe"))

    if not os.path.isfile(chrome_binary):
        print(f"Chrome binary not found at: {chrome_binary}")
        sys.exit(1)

    if not os.path.isfile(driver_binary):
        print(f"ChromeDriver binary not found at: {driver_binary}")
        sys.exit(1)

    chrome_options = Options()
    chrome_options.binary_location = chrome_binary
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(driver_binary)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    print('Opening browser...')
    driver.set_page_load_timeout(10)
    hide()
    driver.get("https://dw.courts.wa.gov/index.cfm?fa=home.atty&terms=accept&flashform=0")
    time.sleep(2)
    driver.refresh()

    html = driver.page_source
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

    ensureFolder("Cases", BASE_PATH)
    ensureFolder(f"Clients {BAR_NUMBER}", SHARED_ROOT)

    user_root = os.path.join(BASE_PATH, BAR_NUMBER)
    ensureFolder(BAR_NUMBER, BASE_PATH)

    for case in caseDetails:
        client = case.get('Client Name', 'Unknown')
        case_num = case.get('Case Number', 'NoCaseNumber')
        case_folder = f"{client}; {case_num}"
        ensureFolder(case_folder, user_root)

    write_cases_to_csv(BAR_NUMBER, caseDetails)

    shared_user_root = os.path.join(SHARED_ROOT, f"Clients {BAR_NUMBER}")
    for case in caseDetails:
        client = case.get('Client Name', 'Unknown')
        case_num = case.get('Case Number', 'NoCaseNumber')
        case_folder = f"{client}; {case_num}"
        ensureFolder(case_folder, shared_user_root)

    driver.quit()
    print("Done!")

if __name__ == "__main__":
    run_main()
