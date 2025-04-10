FROM python:3.9-slim

WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY transaction.py ./
COPY firebase_config.py ./

# Expose port 5003
EXPOSE 5003

# Command to run the application
CMD ["python", "transaction.py"]