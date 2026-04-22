# Stage 1: Build dependencies
FROM python:3.9-slim as builder

WORKDIR /app

# Install build dependencies for C-extensions (like psycopg2 or uvloop)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Final Runtime
FROM python:3.9-slim

WORKDIR /app

# Install runtime-only dependencies (Postgres client and shared libraries)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy the actual application code
COPY . .

# Create and switch to a non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port (Render uses this as documentation)
EXPOSE 8000

# Start the application
# We use 'sh -c' so that the $PORT environment variable assigned by Render 
# is correctly injected into the uvicorn command.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]