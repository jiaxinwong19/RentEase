FROM python:3.9-slim

WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY notification.py .

# Expose the application port
EXPOSE 5010

# Command to run the application
CMD ["python", "notification.py"]