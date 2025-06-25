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
        print("⏳ Waiting for search type dropdown...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "selSearchType")))
        time.sleep(1)

        print("✅ Search type dropdown visible")
        select_element = Select(driver.find_element(By.ID, "selSearchType"))
        select_element.select_by_value("Ubi")

        print("⏳ Waiting for UBI input field...")
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "txtSearchBy")))
        time.sleep(1)

        print(f"⌨️ Entering UBI: {ubi}")
        driver.execute_script(f"document.getElementById('txtSearchBy').value = '{ubi}';")
        driver.execute_script("document.getElementById('txtSearchBy').dispatchEvent(new Event('blur'));")
        time.sleep(1)

        print("🖱️ Clicking Search button...")
        driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "searchButton"))

        print("⏳ Waiting for search results body...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "body")))
        time.sleep(1)

        error_div = driver.find_element(By.ID, "valMsg")
        if error_div.is_displayed() and error_div.text.strip():
            msg = error_div.text.strip()
            print(f"⚠️ Validation error on page: {msg}")
            save_html(driver.page_source, "lni_error_post_submit.html")
            save_screenshot(driver, "lni_error_post_submit.png")
            return False

        print("✅ Search results loaded")
        return True

    except Exception as e:
        print("🚨 Exception during navigation:", e)
        save_html(driver.page_source, "error_navigate_lni.html")
        save_screenshot(driver, "error_navigate_lni.png")
        return False

def parse_contractor_html(html):
    soup = BeautifulSoup(html, "html.parser")
    data = {}

    def get_field(label):
        try:
            cell = soup.find("td", string=lambda s: s and label.lower() in s.lower())
            return cell.find_next_sibling("td").get_text(strip=True) if cell and cell.find_next_sibling("td") else None
        except Exception:
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
    print("🔍 Parsing search results page...")
    contractors = []

    soup = BeautifulSoup(driver.page_source, "html.parser")
    result_items = soup.select("div.resultItem")
    print(f"📦 Initial contractor count: {len(result_items)}")
    save_html(driver.page_source, "lni_list.html")
    save_screenshot(driver, "lni_list.png")

    for i in range(len(result_items)):
        try:
            print(f"\n➡️ Clicking contractor result #{i+1}...")
            elements = driver.find_elements(By.CSS_SELECTOR, "div.resultItem")
            if i >= len(elements):
                print(f"⚠️ Element index {i} out of range")
                continue

            el = elements[i]
            driver.execute_script("arguments[0].scrollIntoView(true);", el)
            WebDriverWait(driver, 10).until(EC.visibility_of(el))
            time.sleep(0.5)

            try:
                el.click()
            except:
                driver.execute_script("arguments[0].click();", el)

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
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "body")))
            time.sleep(1)

        except Exception as e:
            print(f"⚠️ Failed to scrape contractor #{i+1}: {e}")
            save_html(driver.page_source, f"error_detail_{i+1}.html")
            save_screenshot(driver, f"error_detail_{i+1}.png")

    return contractors
