# This image already has Python, Chrome, and the driver installed
FROM joyzoursky/python-selenium:3.9-selenium

# Set up your working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY . .

# Delete the Windows driver to be safe
RUN rm -f chromedriver.exe

# Start your app
CMD ["python", "main.py"]
