# Use Python 3.12 slim image for small footprint
FROM python:3.12-slim

# Install system dependencies needed for some packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better Docker caching)
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy entire application
COPY . .

# Ensure directory exists for ChromaDB
RUN mkdir -p /app/ai_memory

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "app.py"]
