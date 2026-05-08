from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# On this specific Docker image, you don't need to provide a path
driver = webdriver.Chrome(options=options)

