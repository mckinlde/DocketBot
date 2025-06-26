import time
import os
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TEMP_HTML_DIR = os.path.join(os.getcwd(), "temp_html_files")
os.makedirs(TEMP_HTML_DIR, exist_ok=True)

def wait_for_detail_panel(driver, timeout=10):
    try:
        panel = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "ctl00_cphMain_upnlContractor"))
        )
        return panel
    except:
        return None

def get_lni_contractors(driver, ubi):
    print(f"🔍 Parsing search results page...")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "resultItem"))
    )

    result_blocks = driver.find_elements(By.CLASS_NAME, "resultItem")
    print(f"📦 Initial contractor count: {len(result_blocks)}")

    contractors = []
    for i, result in enumerate(result_blocks):
        print(f"\n➡️ Clicking contractor result #{i + 1}...")

        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", result)
            time.sleep(0.5)
            result.click()
            time.sleep(0.5)

            panel = wait_for_detail_panel(driver)
            if not panel:
                raise Exception("Detail panel did not appear")

            time.sleep(1.0)
            html = driver.page_source

            # Save HTML for debug
            detail_path = os.path.join(TEMP_HTML_DIR, f"lni_detail_{i+1}.html")
            with open(detail_path, "w", encoding="utf-8") as f:
                f.write(html)

            contractor = parse_lni_detail_html(html)
            contractors.append(contractor)

        except Exception as e:
            print(f"⚠️ Failed to scrape contractor #{i + 1}: {e}")
            continue

    print("\n✅ LNI Contractor Info:")
    for c in contractors:
        print(c)

    return contractors

def parse_lni_detail_html(html):
    soup = BeautifulSoup(html, "html.parser")

    def get_text_by_label(label):
        label_elem = soup.find("span", string=label)
        if label_elem and label_elem.find_next("span"):
            return label_elem.find_next("span").get_text(strip=True)
        return ""

    contractor = {
        "Registration Number": get_text_by_label("Registration Number:"),
        "Contractor Name": get_text_by_label("Contractor Name:"),
        "Status": get_text_by_label("Status:"),
        "Business Type": get_text_by_label("Business Type:"),
        "Expiration Date": get_text_by_label("Expiration Date:"),
        "Phone Number": get_text_by_label("Phone Number:"),
        "Address": get_text_by_label("Address:"),
        "Email": get_text_by_label("Email:"),
        "Bond": get_text_by_label("Bond:"),
        "Insurance": get_text_by_label("Insurance:"),
        "Suspended": get_text_by_label("Suspended:")
    }

    return contractor
