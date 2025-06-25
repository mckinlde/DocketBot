import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, WebDriverException

from .lni_parser import get_lni_info_from_html
from .utils import wait_for_continue, BASE_DIR

def get_lni_info(driver, ubi):
    try:
        driver.get("https://secure.lni.wa.gov/verify/")
        print("LNI loaded. Use the search box to look up the contractor. Press ENTER when the result list appears.")
        if not wait_for_continue():
            return {"status": "Not found"}

        temp_dir = os.path.join(BASE_DIR, "temp_html_files")
        os.makedirs(temp_dir, exist_ok=True)

        list_path = os.path.join(temp_dir, "lni_list.html")
        with open(list_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"✅ Saved contractor list HTML to: {list_path}")

        list_url = driver.current_url
        contractors = []

        result_divs = driver.find_elements(By.CSS_SELECTOR, "div.resultItem")
        if not result_divs:
            print("ℹ️  No LNI contractor results found.")
            return []

        for idx in range(len(result_divs)):
            try:
                print(f"➡️  Navigating to contractor detail page #{idx + 1}...")
                result_divs = driver.find_elements(By.CSS_SELECTOR, "div.resultItem")
                if idx >= len(result_divs):
                    print(f"⚠️  Skipping contractor #{idx + 1}: DOM changed or index out of bounds.")
                    break

                contractor_elem = result_divs[idx]
                driver.execute_script("arguments[0].scrollIntoView(true);", contractor_elem)
                contractor_elem.click()

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "layoutContainer"))
                )
                time.sleep(5)

                html = driver.page_source
                detail_path = os.path.join(temp_dir, f"lni_detail_{idx + 1}.html")
                with open(detail_path, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"✅ Saved contractor detail HTML #{idx + 1} to: {detail_path}")

                with open(list_path, "r", encoding="utf-8") as list_file:
                    list_html = list_file.read()

                parsed_list = get_lni_info_from_html(list_html, [html])
                if parsed_list:
                    contractors.extend(parsed_list)

            except TimeoutException:
                print(f"⚠️  Contractor detail page #{idx + 1} timed out.")
            except (StaleElementReferenceException, WebDriverException) as e:
                print(f"⚠️  Navigation error: {e}")
            finally:
                driver.get(list_url)
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.resultItem"))
                    )
                except TimeoutException:
                    print("⚠️  Could not return to result list.")
                    break

        return contractors

    except Exception as e:
        print(f"🚨 LNI navigation error: {e}")
        return {"status": "error"}