# lni.py
# Scrapes LNI contractor data given a driver and UBI number.
# Navigates to the contractor search site, fills out the UBI form,
# scrapes the list and each contractor detail page.
# Returns list of dicts with contractor info.
# Not responsible for writing PDFs — returns data to caller.
# lni.py — Updated to click div.resultItem (not <a>) and scrape correct contractor detail

# lni.py — Final fixed version (click logic + parser hardened)
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup

TEMP_DIR = os.path.join(os.path.dirname(__file__), "../temp_html_files")
os.makedirs(TEMP_DIR, exist_ok=True)

def save_html(content, filename):
    path = os.path.join(TEMP_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def save_screenshot(driver, filename):
    path = os.path.join(TEMP_DIR, filename)
    driver.save_screenshot(path)

def navigate_lni(driver, ubi):
    print("🌐 Navigating to LNI...")
    try:
        driver.get("https://secure.lni.wa.gov/verify/")
        print("⏳ Waiting for search type dropdown...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "selSearchType")))
        Select(driver.find_element(By.ID, "selSearchType")).select_by_value("Ubi")
        print("✅ Search type dropdown visible")

        print("⏳ Waiting for UBI input field...")
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "txtSearchBy")))
        driver.find_element(By.ID, "txtSearchBy").clear()
        driver.find_element(By.ID, "txtSearchBy").send_keys(ubi)
        driver.execute_script("document.getElementById('txtSearchBy').dispatchEvent(new Event('blur'));")
        time.sleep(1)

        print("🖱️ Clicking Search button...")
        driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "searchButton"))

        print("⏳ Waiting for search results body...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "body")))
        time.sleep(1)

        error_div = driver.find_element(By.ID, "valMsg")
        if error_div.is_displayed() and error_div.text.strip():
            print(f"⚠️ Validation error: {error_div.text.strip()}")
            save_html(driver.page_source, "lni_error_post_submit.html")
            save_screenshot(driver, "lni_error_post_submit.png")
            return False

        print("✅ Search results loaded")
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
        try:
            cell = soup.find("td", string=lambda s: s and label.lower() in s.lower())
            return cell.find_next_sibling("td").get_text(strip=True) if cell else None
        except Exception:
            return None

    def get_by_id(el_id):
        el = soup.find(id=el_id)
        return el.get_text(strip=True) if el else None

    data["Contractor Name"] = get_by_id("lblBusinessName")
    data["Registration Number"] = get_by_id("lblContLicNum")
    data["UBI"] = get_by_id("lblUBINum")
    data["Bond Company"] = get_field("Bonding Company")
    data["Bond Amount"] = get_field("Bond Amount")
    data["Insurance Company"] = get_field("Insurance Company")
    data["Insurance Amount"] = get_field("Insurance Amount")
    data["Suspended"] = get_by_id("lblSuspended")
    data["Lawsuits"] = get_field("Lawsuits Against Contractor’s Bond")

    return data

def get_lni_contractors(driver):
    print("🔍 Parsing search results page...")
    contractors = []

    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.resultItem")))
    save_html(driver.page_source, "lni_list.html")
    save_screenshot(driver, "lni_list.png")

    search_results_url = driver.current_url
    result_elements = driver.find_elements(By.CSS_SELECTOR, "div.resultItem")
    print(f"📦 Initial contractor count: {len(result_elements)}")

    for i in range(len(result_elements)):
        try:
            print(f"\n➡️ Clicking contractor result #{i+1}...")
            # Refresh list elements each time due to page reload
            result_elements = driver.find_elements(By.CSS_SELECTOR, "div.resultItem")
            el = result_elements[i]

            driver.execute_script("arguments[0].scrollIntoView(true);", el)
            time.sleep(0.5)
            el.click()

            print("⏳ Waiting for contractor detail panel...")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "contractorDetail"))
            )
            time.sleep(1)

            html = driver.page_source
            save_html(html, f"lni_detail_{i+1}.html")
            save_screenshot(driver, f"lni_detail_{i+1}.png")

            parsed = parse_contractor_html(html)
            contractors.append(parsed)
            print(f"✅ Parsed contractor #{i+1}: {parsed.get('Contractor Name', 'Unnamed')}")

            print("🔙 Returning to results list...")
            driver.back()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "body"))
            )
            time.sleep(1)

        except Exception as e:
            print(f"⚠️ Failed to scrape contractor #{i+1}: {e}")
            save_html(driver.page_source, f"error_detail_{i+1}.html")
            save_screenshot(driver, f"error_detail_{i+1}.png")
            continue

    return contractors
