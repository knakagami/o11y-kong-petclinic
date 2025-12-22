# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
# git is required for pip install from GitHub repositories
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install OpenTelemetry instrumentation libraries
# This automatically installs instrumentation for detected packages (LangChain, FastAPI, etc.)
RUN opentelemetry-bootstrap -a install

# Copy application code
COPY app/ ./app/

# Create directory for vector store
RUN mkdir -p /app/vectorstore && chmod 755 /app/vectorstore

# Expose port
EXPOSE 8084

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8084/health')" || exit 1

# Run the application with OpenTelemetry auto-instrumentation
# This wraps the application with zero-code instrumentation
CMD ["opentelemetry-instrument", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8084"]

