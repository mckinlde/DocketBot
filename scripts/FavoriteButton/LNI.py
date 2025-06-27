# scripts/FavoriteButton/lni.py
import os, time, re
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, StaleElementReferenceException

TEMP_HTML_DIR = os.path.join(os.path.dirname(__file__), "..", "temp_html_files")
os.makedirs(TEMP_HTML_DIR, exist_ok=True)

def lni(driver, ubi):
    # First, use a monster function to open the lni page,
    # perform a search by UBI number,
    # navigate to each result's detail page,
    # and save each result's detail page as an HTML file
    contractor_html_list = open_lni_navigate_and_save_results_as_html(driver, ubi)

    # Next, create an empty list for holding parsed information from the HTML files
    parsed_details_list = []
    # For each HTML file we saved
    for detail_path in contractor_html_list:
        # Open it
        print(f"📂 Loading {detail_path} from disk")
        with open(detail_path, "r", encoding="utf-8") as detail_file:
            list_html = detail_file.read()
        # Try to parse it
        print("🔍 Parsing contractor detail HTML...")
        parsed_details = parse_lni_contractor_html(list_html)
        # And add it to the parsed_details_list
        if parsed_details:
            print("Extending contractor list")
            parsed_details_list.extend(parsed_details)

    # Finally, return the parsed_details_list
    return parsed_details_list


# lni navigation and filesaving
def open_lni_navigate_and_save_results_as_html(driver, ubi):
    print("🌐 Navigating to LNI site...")
    driver.get("https://secure.lni.wa.gov/verify/")
    time.sleep(2)

    try:
        # Wait for and set dropdown to UBI search
        print("⏳ Waiting for search type dropdown...")
        dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "selSearchType"))
        )
        Select(dropdown).select_by_value("Ubi")
        time.sleep(2)

        # Enter UBI number
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "txtSearchBy"))
        )
        ubi_input = driver.find_element(By.ID, "txtSearchBy")
        ubi_input.send_keys(ubi)

        # Click Search
        search_btn = driver.find_element(By.ID, "searchButton")
        search_btn.click()
        print("🖱️ Clicked Search button")
        time.sleep(2)  # defensive sleep
        print("⌛ Waiting for a div.resultitem to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.resultItem"))
        )

        # Save result list HTML
        print("💾 Saving search results page...")
        detail_html = driver.page_source
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = os.path.join(TEMP_HTML_DIR, f"lni_search_results_list_{timestamp}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(detail_html)
        
        print("🔍 Parsing search results page...")
        # Save the results list URL for navigating back to
        list_url = driver.current_url
        contractor_detail_html_list = []
        result_divs = driver.find_elements(By.CSS_SELECTOR, "div.resultItem")
        print(f"📦 Found {len(result_divs)} contractor(s): ")
        for result_div in result_divs:
            print(result_div)
        if not result_divs:
            print("ℹ️  No LNI contractor results found.")
            return []

        # TODO: we may be able to end this function here and return the list of div.resultItems to use as static links

        # Click on the first contractor detail panel (already expanded)
        for idx in range(len(result_divs)):
            try:
                print(f"\n➡️  Navigating to contractor detail page #{idx + 1}...")
                if idx >= len(result_divs):
                    print(f"⚠️  Skipping contractor #{idx + 1}: DOM changed or index out of bounds.")
                    break

                contractor_elem = result_divs[idx]
                driver.execute_script("arguments[0].scrollIntoView(true);", contractor_elem)
                contractor_elem.click()
                time.sleep(2)  # defensive sleep

                print("⌛ Waiting for a id.layoutContainer to load...")
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "layoutContainer"))
                )

                print("💾 Saving contractor detail page...")
                html = driver.page_source
                detail_path = os.path.join(TEMP_HTML_DIR, f"lni_detail_{idx + 1}.html")
                with open(detail_path, "w", encoding="utf-8") as f:
                    print(f"🪶 Writing detail HTML to: {detail_path}")
                    f.write(html)
                print(f"✅ Saved contractor detail HTML #{idx + 1} to: {detail_path}")
                # Extend the list of saved HTMLs
                contractor_detail_html_list.extend(detail_path)

            except TimeoutException:
                print(f"⚠️  Contractor detail page #{idx + 1} failed to load expected content.")
            except (StaleElementReferenceException, WebDriverException) as e:
                print(f"⚠️  Contractor #{idx + 1} navigation error: {e}")
            finally:
                print("🏃‍♂️ Return to results list page") 
                driver.get(list_url)
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.resultItem"))
                    )
                except TimeoutException:
                    print("⚠️  Could not return to result list from detail page.")
                    break

        return contractor_detail_html_list

    except Exception as e:
        print(f"🚨 LNI navigation error: {e}")
        return {"status": "error"}


# parse_lni_contractor_html is returning none for everything
#   e.g.:
# {'Business Name': None, 'UBI Number': None, 'Contractor Registration Number': None, 'Bonding Company': None, 'Bond Amount': None, 'Bond Number': None, 'Insurance Company': None, 'Insurance Amount': None, 'Status': None, 'Suspended': None, 'Lawsuits': None}
def parse_lni_contractor_html(html):
    soup = BeautifulSoup(html, "html.parser")
    get = lambda label: soup.find("span", string=label)
    value_after = lambda label: get(label).find_next("span").text.strip() if get(label) else None

    result = {
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

    print(result)
    return(result)

