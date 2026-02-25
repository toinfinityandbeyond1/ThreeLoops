# Use Python 3.12 slim image for small footprint
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better Docker caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire application
COPY . .

# Ensure directory exists for ChromaDB
RUN mkdir -p /app/ai_memory

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "app.py"]
