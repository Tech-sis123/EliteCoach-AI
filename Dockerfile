# Use Python 3.10 slim image
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies directly to system Python
RUN pip install --no-cache-dir -r requirements.txt

# Copy the actual application code
COPY . .

# Create and switch to a non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port
EXPOSE 8000

# Set Python path and start the application
CMD ["sh", "-c", "PYTHONPATH=/app python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]