# scripts/FavoriteButton/lni.py

import os
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TEMP_HTML_DIR = os.path.abspath("temp_html_files")
os.makedirs(TEMP_HTML_DIR, exist_ok=True)

def get_lni_contractors(driver, ubi):
    print("🌐 Navigating to LNI...")
    driver.get("https://secure.lni.wa.gov/verify/")
    time.sleep(10)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_lstSearchBy"))
        )
        print("✅ Search type dropdown visible")
    except Exception as e:
        print("❌ Dropdown not found:", e)
        return []

    # Select 'UBI Number' from dropdown (value='3')
    driver.execute_script("document.getElementById('ctl00_ContentPlaceHolder1_lstSearchBy').value = '3';")
    time.sleep(2)

    # Wait for input and enter UBI
    print("⏳ Waiting for UBI input field...")
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtSearchTerm"))
        )
    except:
        print("❌ UBI input field not found")
        return []

    input_box = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtSearchTerm")
    input_box.clear()
    input_box.send_keys(ubi)
    print(f"⌨️ Entering UBI: {ubi}")
    time.sleep(1)

    # Click search
    print("🖱️ Clicking Search button...")
    driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_btnSearch").click()
    time.sleep(10)

    # Wait for results
    print("⏳ Waiting for search results body...")
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_upnlResults"))
        )
        print("✅ Search results loaded")
    except:
        print("❌ Search results did not load")
        return []

    contractors = []
    print("🔍 Parsing search results page...")

    # Grab the full page HTML and parse it
    html = driver.page_source
    list_path = os.path.join(TEMP_HTML_DIR, "lni_list.html")
    with open(list_path, "w", encoding="utf-8") as f:
        f.write(html)

    soup = BeautifulSoup(html, "html.parser")
    results = soup.find_all("div", class_="resultItem")
    print(f"📦 Initial contractor count: {len(results)}")

    for i in range(len(results)):
        print(f"\n➡️ Clicking contractor result #{i + 1}...")
        try:
            # Find all result items again and click the correct one
            items = driver.find_elements(By.CLASS_NAME, "resultItem")
            items[i].click()
            time.sleep(10)

            detail_html = driver.page_source
            detail_path = os.path.join(TEMP_HTML_DIR, f"lni_detail_{i+1}.html")
            with open(detail_path, "w", encoding="utf-8") as f:
                f.write(detail_html)

            contractor_data = parse_lni_contractor_html(detail_html)
            contractors.append(contractor_data)

            # Return to list
            print("🔙 Returning to list...")
            driver.back()
            time.sleep(10)
        except Exception as e:
            print(f"⚠️ Failed to scrape contractor #{i + 1}: {e}")

    print("✅ LNI Contractor Info:")
    for c in contractors:
        for k, v in c.items():
            print(f" - {k}: {v}")
        print()
    return contractors


def parse_lni_contractor_html(html):
    soup = BeautifulSoup(html, "html.parser")
    get = lambda label: soup.find("span", string=label)
    value_after = lambda label: get(label).find_next("span").text.strip() if get(label) else None

    return {
        "Business Name": value_after("Business Name:"),
        "UBI Number": value_after("UBI Number:"),
        "Contractor Registration Number": value_after("Contractor Registration Number:"),
        "Bonding Company": value_after("Bonding Company:"),
        "Bond Amount": value_after("Bond Amount:"),
        "Bond Number": value_after("Bond Number:"),
        "Insurance Company": value_after("Insurance Company:"),
        "Insurance Amount": value_after("Insurance Amount:"),
        "Status": value_after("Status:"),
        "Suspended": value_after("Suspended:"),
        "Lawsuits": value_after("Lawsuits Filed Against Bond:")
    }
