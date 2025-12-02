# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user
RUN useradd -m -u 1000 appuser

# Set up startup scripts with proper permissions
RUN chmod +x start.sh start_server.py && chown appuser:appuser start.sh start_server.py

# Change ownership of app directory
RUN chown -R appuser:appuser /app
USER appuser

# Expose port (default to 5000, but Railway will override with PORT env var)
EXPOSE 5000

# Run the application using Python startup script (more reliable for PORT handling)
CMD ["python", "start_server.py"]
