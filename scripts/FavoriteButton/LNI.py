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
    # and save links from the search results to their detail pages
    detail_page_links = open_lni_and_get_detail_page_links(driver, ubi)

    
    # navigate to each result's detail page,
    # and save each result's detail page as an HTML file
    filepaths = save_detail_to_html(driver, detail_page_links)

    # Next, create an empty list for holding parsed information from the HTML files
    parsed_details_list = []
    # For each HTML file we saved
    for detail_path in filepaths:
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


# lni ubi search and detail page link grabbing
def open_lni_and_get_detail_page_links(driver, ubi):
    print("🌐 Navigating to LNI site...")
    driver.get("https://secure.lni.wa.gov/verify/")
    time.sleep(2)

    try:
        print("⏳ Waiting for search type dropdown...")
        dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "selSearchType"))
        )
        Select(dropdown).select_by_value("Ubi")
        time.sleep(2)

        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "txtSearchBy"))
        )
        ubi_input = driver.find_element(By.ID, "txtSearchBy")
        ubi_input.send_keys(ubi)

        search_btn = driver.find_element(By.ID, "searchButton")
        search_btn.click()
        print("🖱️ Clicked Search button")
        time.sleep(2)
        print("⌛ Waiting for a div.resultitem to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.resultItem"))
        )

        print("💾 Saving search results page...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = os.path.join(TEMP_HTML_DIR, f"lni_search_results_list_{timestamp}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"✅ Search results page saved to {html_path}")

        soup = BeautifulSoup(driver.page_source, "html.parser")
        result_divs = soup.select("div.resultItem")
        print(f"🔗 Extracting contractor detail URLs from {len(result_divs)} result items...")

        base_detail_url = "https://secure.lni.wa.gov/verify/Detail.aspx?"
        detail_urls = []
        for i, result in enumerate(result_divs, start=1):
            raw_id = result.get("id")
            if raw_id:
                url = base_detail_url + raw_id
                detail_urls.append(url)
                print(f"  #{i}: ✅ {url}")
            else:
                print(f"  #{i}: ❌ No ID attribute found")

        return detail_urls

    except Exception as e:
        print(f"🚨 LNI navigation error: {e}")
        return []
     

# lni detail page opening and html filesaving
def save_detail_to_html(driver, detail_urls):
    contractor_detail_html_list = []
    try:
        for idx, url in enumerate(detail_urls):
            try:
                print(f"\n➡️  Navigating to contractor detail page #{idx + 1}...")
                driver.get(url)
                time.sleep(2)

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

                contractor_detail_html_list.append(detail_path)

            except TimeoutException:
                print(f"⚠️ Contractor detail page #{idx + 1} failed to load expected content.")
            except (StaleElementReferenceException, WebDriverException) as e:
                print(f"⚠️ Contractor #{idx + 1} navigation error: {e}")
        return contractor_detail_html_list

    except Exception as e:
        print(f"🚨 LNI navigation error: {e}")
        return []


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

