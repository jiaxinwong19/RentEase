FROM python:3.9-slim

WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY report_damage.py .

# Expose the application port
EXPOSE 5004

# Command to run the application
CMD ["python", "report_damage.py"]