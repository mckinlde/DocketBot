# lni.py
# lni.py defines utilities that are imported to / called from main.py, which
# provides it a chromedriver and UBI number.
# It waits for teh user to fill out the form and navigate to the list of results,
# where it then gets control returned to it and automatically navigates to each
# result to scrape the necessary information, which it then returns as a dict for 
# output to the console.

# lni.py is not responsible for writing information to a PDF, and is not reliant on 
# HTML tags to navigate the data, which is on a javascript page

# # LNI contractor detail pages now load and extract structured data automatically. The script:
#     Clicks each contractor result element directly.
#     Waits for expected detail content.
#     Saves each page's HTML for debug.
#     Returns to the saved result list URL (instead of using a brittle back button).
# Extracts:
#     Registration number
#     Bond(s) (company, number, amount)
#     Insurance (company, amount)
#     License suspension status
#     Lawsuits (case number, county, parties, status)

#     from the LNI:
#     - Contractors registration number 
#     - bond company, amount, and bond number (sometimes there are more than one)
#     - Insurance company and amount
#     - if contractors license is suspended
#     - any active lawsuits against the bond, case number, county, parites, status 
# lni.py

import os
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMP_HTML_DIR = os.path.join(BASE_DIR, "temp_html_files")
os.makedirs(TEMP_HTML_DIR, exist_ok=True)

def wait_for_user(prompt="Press ENTER to continue after results load (or ';' to skip): "):
    return input(prompt).strip() != ";"


def get_lni_info(driver, ubi):
    try:
        driver.get("https://secure.lni.wa.gov/verify/")
        print("LNI Verify loaded. Use the search box to look up the contractor.")

        if not wait_for_user():
            return []

        list_url = driver.current_url
        list_path = os.path.join(TEMP_HTML_DIR, "lni_list.html")
        with open(list_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"✅ Saved list page to {list_path}")

        results = driver.find_elements(By.CSS_SELECTOR, "div.resultItem")
        if not results:
            print("⚠️ No contractor results found.")
            return []

        contractor_data = []

        for idx in range(len(results)):
            try:
                print(f"\n➡️ Navigating to detail page #{idx + 1}")
                results = driver.find_elements(By.CSS_SELECTOR, "div.resultItem")
                if idx >= len(results):
                    break

                el = results[idx]
                driver.execute_script("arguments[0].scrollIntoView(true);", el)
                time.sleep(1)
                el.click()

                # Wait for detail content to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "layoutContainer"))
                )
                time.sleep(2)

                html = driver.page_source
                html_path = os.path.join(TEMP_HTML_DIR, f"lni_detail_{idx + 1}.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"✅ Saved detail page to {html_path}")

                parsed = parse_lni_detail_html(html)
                contractor_data.append(parsed)

            except TimeoutException:
                print(f"⚠️ Timeout on detail page #{idx + 1}")
            except StaleElementReferenceException:
                print(f"⚠️ StaleElementReference on page #{idx + 1}")
            finally:
                driver.get(list_url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.resultItem"))
                )
                time.sleep(2)

        return contractor_data

    except Exception as e:
        print(f"🚨 Error navigating LNI: {e}")
        return []


def parse_lni_detail_html(html):
    soup = BeautifulSoup(html, "html.parser")
    result = {}

    def extract_kv(label_text):
        row = soup.find("td", string=re.compile(label_text, re.I))
        if row and row.find_next_sibling("td"):
            return row.find_next_sibling("td").get_text(strip=True)
        return None

    result["Registration Number"] = extract_kv("Registration #")
    result["License Suspended"] = extract_kv("License Suspended")
    result["Insurance Company"] = extract_kv("Insurance Company")
    result["Insurance Amount"] = extract_kv("Insurance Amount")

    # Bond Info
    result["Bonds"] = []
    for h4 in soup.find_all("h4", string=re.compile("Bond Information", re.I)):
        table = h4.find_next("table")
        if table:
            for row in table.select("tr")[1:]:
                tds = row.find_all("td")
                if len(tds) >= 3:
                    result["Bonds"].append({
                        "Bonding Company": tds[0].get_text(strip=True),
                        "Bond Number": tds[1].get_text(strip=True),
                        "Amount": tds[2].get_text(strip=True),
                    })

    # Lawsuits
    result["Lawsuits"] = []
    for h4 in soup.find_all("h4", string=re.compile("Lawsuits", re.I)):
        table = h4.find_next("table")
        if table:
            for row in table.select("tr")[1:]:
                tds = row.find_all("td")
                if len(tds) >= 4:
                    result["Lawsuits"].append({
                        "Case Number": tds[0].get_text(strip=True),
                        "County": tds[1].get_text(strip=True),
                        "Parties": tds[2].get_text(strip=True),
                        "Status": tds[3].get_text(strip=True),
                    })

    return result
