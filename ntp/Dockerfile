# Use an official Python base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the main module (nr_module) and pyvolt into the container
COPY ntp /app/ntp

# Install dependencies (if any)
RUN pip install --no-cache-dir -r /app/ntp/requirements.txt

# Set environment variables for InfluxDB

ENV INFLUXDB_URL="http://influxdb:8086"
ENV INFLUXDB_BUCKET="Hello"
ENV INFLUXDB_TOKEN_FILE="/token_storage/token.txt"

# Define volume for token storage
VOLUME /token_storage

# Set the default command to run the script
CMD ["python", "/app/ntp/NTP.py"]