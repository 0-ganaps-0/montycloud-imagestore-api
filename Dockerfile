# Stage 1: Build stage
FROM python:3.12-slim as builder

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for building some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install and use a virtual environment for clean dependency isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production stage
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"
ENV APP_ENV=production

WORKDIR /app

# Create a non-privileged user for security (Standard for 2026 Prod)
RUN adduser --disabled-password --gecos "" appuser

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the source code (Assuming code is in src/ folder)
COPY src/ /app/src/

# Ensure the appuser owns the app directory
RUN chown -R appuser:appuser /app
USER appuser

# Expose the port FastAPI runs on
EXPOSE 8000

# Start the application using Uvicorn
# 0.0.0.0 is required for Docker to route traffic into the container
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
