FROM python:3.9-slim

WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY inventory.py .

# Expose the application port
EXPOSE 5020

# Set the environment variable for Flask
ENV FLASK_APP=inventory.py
ENV FLASK_ENV=production

# Command to run the application
CMD ["python", "inventory.py"]