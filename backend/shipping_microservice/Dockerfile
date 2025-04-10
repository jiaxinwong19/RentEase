FROM python:3.9-slim

WORKDIR /app

# Install netcat for checking network connectivity
RUN apt-get update && apt-get install -y netcat-openbsd && apt-get clean

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY shipping_service.py .

# Set environment variables
ENV PORT=5009
ENV DEBUG=true
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5009

# Run the application with unbuffered output
CMD ["python", "-u", "shipping_service.py"]