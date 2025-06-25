import os

SCRIPT_PATH = os.path.abspath(__file__)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(SCRIPT_PATH), "../.."))
CHROME_BINARY = os.path.join(BASE_DIR, "chrome-win64", "chrome.exe")
CHROMEDRIVER_BINARY = os.path.join(BASE_DIR, "chromedriver-win64", "chromedriver.exe")
PDF_TEMPLATE = os.path.join(BASE_DIR, "assets", "0000 New Matter Form.pdf")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_HTML_DIR = os.path.join(BASE_DIR, "temp_html_files")

for path in [OUTPUT_DIR, TEMP_HTML_DIR]:
    if not os.path.exists(path):
        os.makedirs(path)
