# lni.py
# Scrapes LNI contractor data given a driver and UBI number.
# Navigates to the contractor search site, fills out the UBI form,
# scrapes the list and each contractor detail page.
# Returns list of dicts with contractor info.
# Not responsible for writing PDFs — returns data to caller.
# lni.py — Updated to click div.resultItem (not <a>) and scrape correct contractor detail

# lni.py – Final working version
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup

TEMP_DIR = os.path.join(os.path.dirname(__file__), "../temp_html_files")
os.makedirs(TEMP_DIR, exist_ok=True)

def save_html(html, filename):
    path = os.path.join(TEMP_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"📄 Saved HTML snapshot: {path}")

def save_screenshot(driver, filename):
    path = os.path.join(TEMP_DIR, filename)
    driver.save_screenshot(path)
    print(f"🖼️ Saved screenshot: {path}")

def navigate_lni(driver, ubi):
    print("🌐 Navigating to LNI...")
    try:
        driver.get("https://secure.lni.wa.gov/verify/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "selSearchType")))
        time.sleep(1)

        print("✅ Dropdown loaded")
        Select(driver.find_element(By.ID, "selSearchType")).select_by_value("Ubi")

        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "txtSearchBy")))
        time.sleep(1)

        print(f"⌨️ Entering UBI: {ubi}")
        driver.execute_script(f"document.getElementById('txtSearchBy').value = '{ubi}';")
        driver.execute_script("document.getElementById('txtSearchBy').dispatchEvent(new Event('blur'));")
        time.sleep(1)

        print("🖱️ Submitting form...")
        driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "searchButton"))
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "body")))
        time.sleep(1)

        error_div = driver.find_element(By.ID, "valMsg")
        if error_div.is_displayed() and error_div.text.strip():
            msg = error_div.text.strip()
            print(f"⚠️ Validation error: {msg}")
            save_html(driver.page_source, "lni_error_post_submit.html")
            save_screenshot(driver, "lni_error_post_submit.png")
            return False

        print("✅ Results page loaded")
        return True
    except Exception as e:
        print("🚨 Navigation error:", e)
        save_html(driver.page_source, "error_navigate_lni.html")
        save_screenshot(driver, "error_navigate_lni.png")
        return False

def parse_contractor_html(html):
    soup = BeautifulSoup(html, "html.parser")
    data = {}

    def get_field(label):
        cell = soup.find("td", string=lambda s: s and label.lower() in s.lower())
        if cell and cell.find_next_sibling("td"):
            return cell.find_next_sibling("td").get_text(strip=True)
        return None

    def get_by_id(element_id):
        el = soup.find(id=element_id)
        return el.get_text(strip=True) if el else None

    data["Contractor Name"] = get_by_id("lblBusinessName")
    data["Registration Number"] = get_field("Registration Number")
    data["Bonding Company"] = get_field("Bonding Company")
    data["Bond Amount"] = get_field("Bond Amount")
    data["Insurance Company"] = get_field("Insurance Company")
    data["Insurance Amount"] = get_field("Insurance Amount")
    data["Suspended"] = get_field("Suspended")
    data["Lawsuits"] = get_field("Lawsuits Against This Bond")

    return data

def get_lni_contractors(driver):
    print("🔍 Extracting contractors from list...")
    contractors = []

    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.resultItem")))
    result_items = driver.find_elements(By.CSS_SELECTOR, "div.resultItem")

    save_html(driver.page_source, "lni_list.html")
    save_screenshot(driver, "lni_list.png")
    print(f"📦 Found {len(result_items)} contractor(s)")

    for i, item in enumerate(result_items):
        try:
            print(f"\n➡️ Expanding contractor #{i+1}...")
            driver.execute_script("arguments[0].scrollIntoView(true);", item)
            ActionChains(driver).move_to_element(item).click().perform()

            WebDriverWait(item, 5).until(
                lambda d: item.find_element(By.CLASS_NAME, "contractorDetails").is_displayed()
            )
            time.sleep(1)

            html = item.get_attribute("innerHTML")
            html_wrapped = f"<html><body>{html}</body></html>"

            save_html(html_wrapped, f"lni_detail_{i+1}.html")
            save_screenshot(driver, f"lni_detail_{i+1}.png")

            parsed = parse_contractor_html(html_wrapped)
            contractors.append(parsed)
            print(f"✅ Parsed contractor #{i+1}: {parsed.get('Contractor Name', 'Unnamed')}")

        except Exception as e:
            print(f"⚠️ Error parsing contractor #{i+1}: {e}")
            save_html(driver.page_source, f"error_detail_{i+1}.html")
            save_screenshot(driver, f"error_detail_{i+1}.png")

    return contractors
