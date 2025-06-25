from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
from utils import wait_for_continue

def get_sos_info(driver, ubi):
    try:
        driver.get(f"https://ccfs.sos.wa.gov/#/BusinessSearch/UBI/{ubi}")
        print("SOS loaded. Press ENTER after navigating to the detail view.", end="")
        if not wait_for_continue():
            return {"status": "Not found"}

        soup = BeautifulSoup(driver.page_source, "html.parser")
        data = {"ubi": ubi}

        # General info table
        table = soup.find("table", {"class": "table table-striped"})
        if table:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).lower()
                    val = cells[1].get_text(strip=True)
                    if "business name" in key:
                        data["company_name"] = val
                    elif "business type" in key:
                        data["business_type"] = val
                    elif "status" in key:
                        data["business_status"] = val
                    elif "formation date" in key:
                        data["formation_date"] = val
                    elif "expiration date" in key:
                        data["expiration_date"] = val
                    elif "jurisdiction" in key:
                        data["jurisdiction"] = val
                    elif "duration" in key:
                        data["duration"] = val
                    elif "nature of business" in key:
                        data["nature_of_business"] = val

        # Addresses
        address_tags = soup.find_all("div", class_="col-md-6")
        for tag in address_tags:
            header = tag.find("strong")
            if header:
                header_text = header.get_text(strip=True).lower()
                addr_text = tag.get_text(separator=" ", strip=True).replace(header.get_text(strip=True), "").strip()
                if "principal office street address" in header_text:
                    data["principal_street_address"] = addr_text
                elif "mailing address" in header_text:
                    data["mailing_address"] = addr_text
                elif "agent street" in header_text:
                    data["agent_street"] = addr_text
                elif "agent mailing" in header_text:
                    data["agent_mailing"] = addr_text

        # Registered agent
        agent_tag = soup.find("div", id="registered-agent")
        if agent_tag:
            name_span = agent_tag.find("span", class_="ng-binding")
            if name_span:
                data["registered_agent_name"] = name_span.get_text(strip=True)

        # Governors
        governors = []
        gov_table = soup.find("table", id="governor-table")
        if gov_table:
            for row in gov_table.select("tr")[1:]:
                cols = row.select("td")
                if cols:
                    name = cols[0].get_text(strip=True)
                    if name:
                        governors.append(name)
        data["governors"] = governors

        print("\n--- SOS PARSED INFO ---")
        for key, val in data.items():
            print(f"{key}: {val}")

        return data
    except Exception as e:
        print(f"SOS error: {e}")
        return {"status": "error"}
