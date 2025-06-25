# lni.py
import os
import re
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, WebDriverException
from scripts.config import TEMP_HTML_DIR
from scripts.common import wait_for_continue


def get_lni_info(driver, ubi):
    try:
        driver.get("https://secure.lni.wa.gov/verify/")
        print("LNI loaded. Use the search box to look up the contractor. Press ENTER when the result list appears.")
        if not wait_for_continue():
            return {"status": "Not found"}

        list_path = os.path.join(TEMP_HTML_DIR, "lni_list.html")
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
                print(f"\n➡️  Navigating to contractor detail page #{idx + 1}...")

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
                detail_path = os.path.join(TEMP_HTML_DIR, f"lni_detail_{idx + 1}.html")
                with open(detail_path, "w", encoding="utf-8") as f:
                    print(f"🪶 Writing detail HTML to: {detail_path}")
                    f.write(html)
                print(f"✅ Saved contractor detail HTML #{idx + 1} to: {detail_path}")

                with open(list_path, "r", encoding="utf-8") as list_file:
                    list_html = list_file.read()

                parsed_list = get_lni_info_from_html(list_html, [html])
                if parsed_list:
                    contractors.extend(parsed_list)

            except TimeoutException:
                print(f"⚠️  Contractor detail page #{idx + 1} failed to load expected content.")
            except (StaleElementReferenceException, WebDriverException) as e:
                print(f"⚠️  Contractor #{idx + 1} navigation error: {e}")
            finally:
                driver.get(list_url)
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.resultItem"))
                    )
                except TimeoutException:
                    print("⚠️  Could not return to result list from detail page.")
                    break

        return contractors

    except Exception as e:
        print(f"🚨 LNI navigation error: {e}")
        return {"status": "error"}


def get_lni_info_from_html(list_html: str, detail_htmls: list[str]) -> list[dict]:
    contractors = []
    list_soup = BeautifulSoup(list_html, "html.parser")
    print(f"Found {len(list_soup.select('div.resultItem'))} contractor result(s).")

    for idx, detail_html in enumerate(detail_htmls):
        soup = BeautifulSoup(detail_html, "html.parser")
        info = {}

        contractor_name_tag = soup.select_one("div.hdrText")
        contractor_name = contractor_name_tag.get_text(strip=True) if contractor_name_tag else f"Contractor #{idx + 1}"
        print(f"\n📄 {contractor_name} Detail Page:")

        for table in soup.select("table"):
            for row in table.select("tr"):
                cols = row.find_all("td")
                if len(cols) >= 2:
                    label = cols[0].get_text(strip=True).rstrip(":")
                    value = cols[1].get_text(strip=True)

                    if "Registration #" in label:
                        info["Registration Number"] = value
                    elif "License Suspended" in label:
                        info["License Suspended"] = value
                    elif "Insurance Company" in label:
                        info["Insurance Company"] = value
                    elif "Insurance Amount" in label:
                        info["Insurance Amount"] = value

        bonds = []
        for h4 in soup.find_all("h4", string=re.compile("Bond Information", re.I)):
            bond_table = h4.find_next("table")
            if bond_table:
                for row in bond_table.select("tr")[1:]:
                    cols = [td.get_text(strip=True) for td in row.select("td")]
                    if len(cols) >= 3:
                        bonds.append({
                            "Bonding Company": cols[0],
                            "Bond Number": cols[1],
                            "Amount": cols[2],
                        })
        if bonds:
            info["Bonds"] = bonds

        lawsuits = []
        for h4 in soup.find_all("h4", string=re.compile("Lawsuits", re.I)):
            lawsuit_table = h4.find_next("table")
            if lawsuit_table:
                for row in lawsuit_table.select("tr")[1:]:
                    cols = [td.get_text(strip=True) for td in row.select("td")]
                    if len(cols) >= 4:
                        lawsuits.append({
                            "Case Number": cols[0],
                            "County": cols[1],
                            "Parties": cols[2],
                            "Status": cols[3],
                        })
        if lawsuits:
            info["Lawsuits"] = lawsuits

        if info:
            contractors.append(info)
            for key, val in info.items():
                if isinstance(val, list):
                    print(f"  {key}: {len(val)} item(s)")
                    for item in val:
                        print(f"    • {item}")
                else:
                    print(f"  {key}: {val}")
        else:
            print("⚠️  No contractor data extracted from this page.")

    return contractors
