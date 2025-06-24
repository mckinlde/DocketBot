from selenium import webdriver
import time
import random
from bs4 import BeautifulSoup
import os
import csv
from pathlib import Path
import sys

# --- CONFIG ---
NIX_OS = False
CHROME_DRIVER_PATH = "C:/Users/stace/Documents/Python Scripts/chromedriver.exe"
BASE_PATH = 'C:\\Users\\stace\\Desktop\\1 STATE CRIMINAL\\Cases'
SHARED_ROOT = 'C:\\Users\\stace\\Desktop\\SSMC Discovery and Offers'


# --- UTILS ---
def hide():
    time.sleep(random.randint(0, 2) + random.random())


def normalize(s):
    """Remove whitespace, make uppercase, remove invisible characters."""
    return ''.join(s.split()).upper()


def ensureFolder(folder_name, base_path):
    new_directory = os.path.join(base_path, folder_name)
    if not os.path.exists(new_directory):
        os.makedirs(new_directory)
        print('Created folder: ' + new_directory)
    return


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
        result["Appointment Date"] = None

    items = soup.find_all("div", class_="dw-cal-result-item")
    for item in items:
        label = item.find("div", class_="dw-cal-result-label").text.strip(": ")
        data = item.find("div", class_="dw-cal-result-data").text.strip()
        if label == "Case Number":
            data = data.split(' ')[0]
        result[label] = data

    return result

def count_csv_rows(filepath):
    """
    Counts the number of rows in a CSV file.
    Includes the header row if present.
    """
    with open(filepath, 'r', newline='') as file:
        reader = csv.reader(file)
        row_count = sum(1 for row in reader)
    return row_count

def write_cases_to_csv(person, cases):
    # debug metrics
    initial_length, final_length, added, skipped_duplicate = 0, 0, 0, 0
    # make sure encoding always matches
    encoding = 'utf-7'
    # make directory if not exists
    person_dir = os.path.join(BASE_PATH, person)
    os.makedirs(person_dir, exist_ok=True)
    # make CSV if not exists
    csv_path = os.path.join(person_dir, f'{person}Cases.csv')
    # placeholder for already seen cases
    seen = set()

    # Count rows before running
    initial_length = count_csv_rows(csv_path)

    # Load existing keys
    if os.path.isfile(csv_path):
        print(f'{person}Cases.csv exists, at: \n{csv_path}\n')
        with open(csv_path, 'r', newline='', encoding=encoding) as f:
            print(f'Opened Read with encoding {encoding}')
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    client_name = normalize(row[0])
                    case_num = normalize(row[1])
                    seen.add((client_name, case_num))
        # The file is automatically closed here, even if an error occurred within the 'with' block.
    else:
        print(f"{person}Cases.csv doesn't exist, creating new file")
    
    # Write new cases
    file_mode = 'a' if os.path.isfile(csv_path) else 'w'
    with open(csv_path, file_mode, newline='', encoding=encoding) as csvfile:
        print(f'Opened Write with encoding {encoding}')
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        if file_mode == 'w':
            writer.writerow(['Client Name', 'Case Number', 'Date', 'Case Count'])

        for case in cases:
            client_name = normalize(case.get('Client Name', ''))
            case_num = normalize(case.get('Case Number', ''))
            key = (client_name, case_num)

            if key not in seen:
                writer.writerow([
                    case.get('Client Name', '').strip(),
                    case.get('Case Number', '').strip(),
                    "",  # Placeholder for Date
                    ""   # Placeholder for Case Count
                ])
                seen.add(key)
                #print(f"Case {key} added to {person}Cases.csv")
                added += 1
            else:
                #print(f"Case {key} is already in {person}Cases.csv")
                skipped_duplicate += 1
    # The file is automatically closed here, even if an error occurred within the 'with' block.
          
    # Count rows after running
    final_length = count_csv_rows(csv_path)
    # Print debug
    print(f'''
initial_length:     {initial_length};
final_length:       {final_length}; 
added:              {added}; 
skipped_duplicates: {skipped_duplicate};
          ''')

# --- MAIN SCRIPT START ---
print('Opening robot chrome window')

if NIX_OS:
    from scraper.browser import get_driver
    driver = get_driver()
else:
    driver = webdriver.Chrome(CHROME_DRIVER_PATH)

driver.set_page_load_timeout(10)
hide()
driver.get("https://dw.courts.wa.gov/index.cfm?fa=home.atty&terms=accept&flashform=0")

time.sleep(2)
captcha_filled = input('Are we filling for Doug or Stacey? Complete captcha, then type d/s and press enter: ')
driver.refresh()

doug = stacey = False
if captcha_filled == 'd':
    doug = True
elif captcha_filled == 's':
    stacey = True
else:
    print('Error: need you to input a d or s')
    driver.quit()
    exit(1)

html = driver.page_source
soup = BeautifulSoup(html, "lxml")

caseSoups = soup.find_all("div", class_="dw-search-result std-vertical-med-margin dw-cal-search-result")

print(f'''
Cases found online, 
before filtering for Sunnyside Court:
{len(caseSoups)}''')

# Filter for just Sunnyside Municipal Court cases
caseDetails = []
for case_soup in caseSoups:
    details = parseCase(case_soup)
    if details.get("Court") != "SUNNYSIDE MUNICIPAL":
        continue
    # print(details)
    caseDetails.append(details)

print(f'''
After filtering for Sunnyside:
{len(caseDetails)}
''')

# Create folder structure
ensureFolder('Cases', 'C:\\Users\\stace\\Desktop\\1 STATE CRIMINAL')
ensureFolder('Clients Stacey McKinley', SHARED_ROOT)
ensureFolder('Clients Doug McKinley', SHARED_ROOT)

if stacey:
    attorney_root = os.path.join(BASE_PATH, "Stacey")
    ensureFolder("Stacey", BASE_PATH)
    for case in caseDetails:
        client = case.get('Client Name', 'Unknown')
        case_num = case.get('Case Number', 'NoCaseNumber')
        case_folder = f"{client}; {case_num}"
        ensureFolder(case_folder, attorney_root)

    write_cases_to_csv('Stacey', caseDetails)

    shared_attorney_root = os.path.join(SHARED_ROOT, "Clients Stacey McKinley")
    for case in caseDetails:
        client = case.get('Client Name', 'Unknown')
        case_num = case.get('Case Number', 'NoCaseNumber')
        case_folder = f"{client}; {case_num}"
        ensureFolder(case_folder, shared_attorney_root)

    input('Done! Press enter to close the robot.')
    driver.quit()

elif doug:
    attorney_root = os.path.join(BASE_PATH, "Doug")
    ensureFolder("Doug", BASE_PATH)
    for case in caseDetails:
        client = case.get('Client Name', 'Unknown')
        case_num = case.get('Case Number', 'NoCaseNumber')
        case_folder = f"{client}; {case_num}"
        ensureFolder(case_folder, attorney_root)

    write_cases_to_csv('Doug', caseDetails)

    shared_attorney_root = os.path.join(SHARED_ROOT, "Clients Doug McKinley")
    for case in caseDetails:
        client = case.get('Client Name', 'Unknown')
        case_num = case.get('Case Number', 'NoCaseNumber')
        case_folder = f"{client}; {case_num}"
        ensureFolder(case_folder, shared_attorney_root)

    input('Done! Press enter to close the robot.')
    driver.quit()
