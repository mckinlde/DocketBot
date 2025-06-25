# sos.py
from selenium.webdriver.common.by import By
from scripts.common import wait_for_continue

def get_sos_info(driver, ubi):
    try:
        driver.get(f"https://ccfs.sos.wa.gov/#/BusinessSearch/UBI/{ubi}")
        print("SOS loaded. Press ENTER after navigating to the detail view.", end="")
        if not wait_for_continue():
            return {"status": "Not found"}

        # TODO: Add actual live scraping
        data = {
            "company_name": "OMAK MACHINE SHOP, INC.",
            "ubi": ubi,
            "business_type": "WA PROFIT CORPORATION",
            "business_status": "ACTIVE",
            "principal_street_address": "505 OKOMA DR, OMAK, WA, 98841, UNITED STATES",
            "mailing_address": "PO BOX 1625, OMAK, WA, 98841-1625, UNITED STATES",
            "expiration_date": "01/31/2026",
            "jurisdiction": "UNITED STATES, WASHINGTON",
            "formation_date": "01/03/1975",
            "duration": "PERPETUAL",
            "nature_of_business": "OTHER SERVICES, DOMESTIC AND IRRIGATION PUMP INSTALLER",
            "registered_agent_name": "DARYN K APPLE",
            "agent_street": "505 OKOMA DR, OMAK, WA, 98841-9251, UNITED STATES",
            "agent_mailing": "PO BOX 1625, OMAK, WA, 98841-1625, UNITED STATES",
            "governors": ["DARYN APPLE", "LISA APPLE"],
        }

        print("\n--- SOS DEBUG INFO ---")
        for key, val in data.items():
            print(f"{key}: {val}")

        return data
    except Exception as e:
        print(f"SOS error: {e}")
        return {"status": "error"}
