# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set a working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . /app/

# Expose port 5000
EXPOSE 5005

# Set the command to run the service
CMD ["python", "app.py"]
