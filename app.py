from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# This image has chrome installed at /usr/bin/google-chrome
options.binary_location = "/usr/bin/google-chrome"

driver = webdriver.Chrome(options=options)
