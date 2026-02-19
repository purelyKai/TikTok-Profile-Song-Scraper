# Use Playwright's official Python image with browsers pre-installed
FROM mcr.microsoft.com/playwright/python:v1.50.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium)
RUN playwright install chromium

# Copy application code
COPY scraper.py processor.py main.py ./

# Create output directory
RUN mkdir -p /app/output

# Set environment variables for Docker
ENV HEADLESS=true
ENV PYTHONUNBUFFERED=1

# Run the main script
CMD ["python", "-u", "main.py"]
