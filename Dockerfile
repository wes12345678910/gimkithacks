# 1. Use a more stable Python base
FROM python:3.9-slim

# 2. Install essential tools and Google Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    curl \
    --no-install-recommends \
    && wget -q -O - https://google.com | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg \
    && sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://google.com stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 3. Setup work directory
WORKDIR /app

# 4. Copy requirements first (improves build speed)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your code and cleanup
COPY . .
RUN rm -f chromedriver.exe

# 6. Start command
CMD ["python", "main.py"]
