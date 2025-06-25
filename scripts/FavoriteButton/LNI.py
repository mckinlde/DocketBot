# lni.py
# Scrapes LNI contractor data given a driver and UBI number.
# Navigates to the contractor search site, fills out the UBI form,
# scrapes the list and each contractor detail page.
# Returns list of dicts with contractor info.
# Not responsible for writing PDFs — returns data to caller.
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
        input_box = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "txtSearchBy"))
        )
        time.sleep(1)

        input_box.clear()
        input_box.send_keys(ubi)
        print(f"✅ UBI '{ubi}' entered")

        print("🖱️ Clicking Search button...")
        driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "searchButton"))

        print("⏳ Waiting for search results body...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "body")))
        time.sleep(1)

        # Check for validation error
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

    def get_text(label):
        tag = soup.find("td", string=lambda s: s and label.lower() in s.lower())
        if tag and tag.find_next_sibling("td"):
            return tag.find_next_sibling("td").get_text(strip=True)
        return None

    data["Contractor Name"] = soup.find("span", id="lblBusinessName")
    if data["Contractor Name"]:
        data["Contractor Name"] = data["Contractor Name"].get_text(strip=True)

    data["Registration Number"] = get_text("Registration Number")
    data["Bonding Company"] = get_text("Bonding Company")
    data["Bond Amount"] = get_text("Bond Amount")
    data["Insurance Company"] = get_text("Insurance Company")
    data["Insurance Amount"] = get_text("Insurance Amount")
    data["Suspended"] = get_text("Suspended")
    data["Lawsuits"] = get_text("Lawsuits Against This Bond")

    return data

def get_lni_contractors(driver):
    print("🔍 Parsing search results page...")
    contractors = []

    # Snapshot 1: raw contractor list page
    soup = BeautifulSoup(driver.page_source, "html.parser")
    result_items = soup.select("div.resultItem")
    print(f"📦 Initial contractor count: {len(result_items)}")
    save_html(driver.page_source, "lni_list.html")
    save_screenshot(driver, "lni_list.png")

    # Defensive re-fetch if none found
    if not result_items:
        print("⚠️ No contractor items found; retrying after brief wait...")
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        result_items = soup.select("div.resultItem")
        print(f"📦 Contractor count after retry: {len(result_items)}")

    for i, _ in enumerate(result_items):
        try:
            print(f"\n➡️ Clicking contractor result #{i+1}...")
            result_div = driver.find_elements(By.CSS_SELECTOR, "div.resultItem")[i]
            driver.execute_script("arguments[0].click();", result_div)

            print("⏳ Waiting for detail page load...")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "body")))
            time.sleep(1)

            html = driver.page_source
            save_html(html, f"lni_detail_{i+1}.html")
            save_screenshot(driver, f"lni_detail_{i+1}.png")

            parsed = parse_contractor_html(html)
            contractors.append(parsed)

            print(f"✅ Parsed contractor #{i+1}: {parsed.get('Contractor Name', 'Unnamed')}")

            print("🔙 Returning to results list...")
            driver.execute_script("window.location.href = document.referrer;")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "body")))
            time.sleep(1)

        except Exception as e:
            print(f"⚠️ Failed to scrape contractor #{i+1}: {e}")
            save_html(driver.page_source, f"error_detail_{i+1}.html")
            save_screenshot(driver, f"error_detail_{i+1}.png")

    return contractors
