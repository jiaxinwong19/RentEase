FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and env file
COPY order_composite.py .
COPY local.env .

# Expose port 5001
EXPOSE 5001

# Run the application
CMD ["python", "order_composite.py"]