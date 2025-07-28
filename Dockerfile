
FROM --platform=linux/amd64 python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y             build-essential             libjpeg62-turbo-dev             zlib1g-dev             libffi-dev             && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Create directories
RUN mkdir -p /app/input /app/output /app/models

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port for web interface (optional)
EXPOSE 8000

# Make main.py executable
RUN chmod +x main.py

# Default command
ENTRYPOINT ["python", "main.py"]
