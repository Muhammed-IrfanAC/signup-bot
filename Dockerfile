# Use Python 3.10 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY signup_bot/ ./signup_bot/
COPY run.py .
COPY run_api.py .
COPY encode_firebase.py .

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=prod

# Expose port for API
EXPOSE 8080

# Run the bot by default
CMD ["python", "run.py"]
