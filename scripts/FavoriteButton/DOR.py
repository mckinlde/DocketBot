# dor.py
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import wait_for_continue


def get_dor_info(driver):
    try:
        driver.get("https://secure.dor.wa.gov/gteunauth/_/#1")
        print("DOR loaded. Complete CAPTCHA and select business, then ENTER.", end="")
        if not wait_for_continue():
            return {"status": "Not found"}

        # Placeholder return until scraper is implemented
        return {"status": "Not implemented"}

    except Exception as e:
        print(f"DOR error: {e}")
        return {"status": "error"}
