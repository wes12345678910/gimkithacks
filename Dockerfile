# 1. Use Python 3.9 as the base
FROM python:3.9-slim

# 2. Install Chrome and dependencies (needed for Selenium/Scraping)
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 3. Set up your working directory
WORKDIR /app

# 4. Copy your requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your code
COPY . .

# 6. Delete the Windows .exe (we use the Linux one installed in step 2)
RUN rm -f chromedriver.exe

# 7. Start your app
CMD ["python", "main.py"]
