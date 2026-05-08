# 1. Use Python 3.9
FROM python:3.9-slim

# 2. Install dependencies + Add Google Chrome Repository
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl \
    && wget -q -O - https://google.com | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://google.com stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 3. Set up working directory
WORKDIR /app

# 4. Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your code
COPY . .

# 6. Delete the Windows driver if it's there
RUN rm -f chromedriver.exe

# 7. Start your app
CMD ["python", "main.py"]
