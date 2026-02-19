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
COPY app/ ./app/
COPY cli.py .

# Create output directory
RUN mkdir -p /app/output

# Set environment variables
ENV HEADLESS=true
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the FastAPI server
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
