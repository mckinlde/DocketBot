# sos.py
#     From the secretary of state's corporate lookup:
#     - company name
#     - company addresses, mailing, and street
#     - if the company is currently active, and if not, the date of their inactivity
#     - Name of registered agent, and registered agent mailing and street address
#     - Governor names

def wait_for_continue(prompt="Press ENTER to continue, or ';' to skip."):
    resp = input(prompt)
    if resp.strip() == ";":
        return False
    return True

# --- SCRAPERS ---
# ... [existing imports and config remain unchanged above this line] ...

def get_sos_info(driver, ubi):
    try:
        driver.get(f"https://ccfs.sos.wa.gov/#/BusinessSearch/UBI/{ubi}")
        print("SOS loaded. Press ENTER after navigating to the detail view.", end="")
        if not wait_for_continue():
            return {"status": "Not found"}

        # TODO: Add live scraping here — this is from debug HTML for now
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

