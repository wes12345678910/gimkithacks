# 1. Use the official Selenium/Chrome image (most reliable for scraping)
FROM selenium/standalone-chrome:latest

# 2. Switch to root to install Python
USER root
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

# 3. Setup work directory
WORKDIR /app

# 4. Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 5. Copy your code and cleanup
COPY . .
RUN rm -f chromedriver.exe

# 6. Start command (using python3)
CMD ["python3", "main.py"]
