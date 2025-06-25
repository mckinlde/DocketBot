from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from .config import CHROME_BINARY, CHROMEDRIVER_BINARY

def init_driver():
    options = Options()
    options.binary_location = CHROME_BINARY
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(CHROMEDRIVER_BINARY), options=options)
