# lni.py
# Defines get_lni_info(driver, ubi) for use in FavoriteButton workflows.
# Automatically fills out the LNI UBI search form, navigates to each contractor detail page,
# extracts relevant info (including bonds, lawsuits), and returns structured data.
# LNI.py# LNI.py — Auto-fills UBI form, scrapes contractor detail pages, and saves HTML at each step for debugging

import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMP_HTML_DIR = os.path.join(BASE_DIR, "temp_html_files")
os.makedirs(TEMP_HTML_DIR, exist_ok=True)

def save_html_snapshot(driver, name):
    """Save current page source to TEMP_HTML_DIR with the given filename."""
    try:
        path = os.path.join(TEMP_HTML_DIR, f"{name}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"📄 Saved HTML snapshot: {path}")
    except Exception as e:
        print(f"❌ Failed to save HTML snapshot {name}: {e}")

def get_lni_info(driver, ubi):
    try:
        driver.get("https://secure.lni.wa.gov/verify/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ctl00_cphMainContent_ddlSearchType")))
        save_html_snapshot(driver, "landing_page")

        # Step 1: Select "UBI Number" from dropdown
        dropdown = Select(driver.find_element(By.ID, "ctl00_cphMainContent_ddlSearchType"))
        dropdown.select_by_visible_text("UBI Number")
        time.sleep(1)
        save_html_snapshot(driver, "after_select_ubi")

        # Step 2: Enter UBI number
        ubi_input = driver.find_element(By.ID, "ctl00_cphMainContent_txtSearch")
        ubi_input.clear()
        ubi_input.send_keys(ubi)
        time.sleep(1)
        save_html_snapshot(driver, "after_enter_ubi")

        # Step 3: Click the Search button
        search_btn = driver.find_element(By.ID, "ctl00_cphMainContent_btnSearch")
        search_btn.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.resultItem"))
        )
        save_html_snapshot(driver, "after_search")

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

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "layoutContainer"))
                )
                time.sleep(2)

                html = driver.page_source
                html_path = os.path.join(TEMP_HTML_DIR, f"lni_detail_{idx + 1}.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"✅ Saved detail page to {html_path}")

                parsed = parse_lni_detail_dom(driver)
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
        save_html_snapshot(driver, "error_page")
        return []

def parse_lni_detail_dom(driver):
    def get_text_by_label(label):
        try:
            lbl = driver.find_element(By.XPATH, f"//label[contains(text(), '{label}')]")
            value = lbl.find_element(By.XPATH, "../following-sibling::*[1]")
            return value.text.strip()
        except:
            return None

    result = {
        "Registration Number": get_text_by_label("Registration #"),
        "License Suspended": get_text_by_label("License Suspended"),
        "Insurance Company": get_text_by_label("Insurance Company"),
        "Insurance Amount": get_text_by_label("Insurance Amount"),
        "Bonds": [],
        "Lawsuits": []
    }

    try:
        bond_tables = driver.find_elements(By.XPATH, "//h4[contains(text(),'Bond Information')]/following-sibling::table[1]")
        for table in bond_tables:
            rows = table.find_elements(By.XPATH, ".//tr[position()>1]")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    result["Bonds"].append({
                        "Bonding Company": cells[0].text.strip(),
                        "Bond Number": cells[1].text.strip(),
                        "Amount": cells[2].text.strip(),
                    })
    except:
        pass

    try:
        lawsuit_tables = driver.find_elements(By.XPATH, "//h4[contains(text(),'Lawsuits')]/following-sibling::table[1]")
        for table in lawsuit_tables:
            rows = table.find_elements(By.XPATH, ".//tr[position()>1]")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 4:
                    result["Lawsuits"].append({
                        "Case Number": cells[0].text.strip(),
                        "County": cells[1].text.strip(),
                        "Parties": cells[2].text.strip(),
                        "Status": cells[3].text.strip(),
                    })
    except:
        pass

    return result
