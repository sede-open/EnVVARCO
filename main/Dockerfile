# Use an official Python base image
FROM python:3.9-slim

# Copy the main module (nr_module) and pyvolt into the container
COPY main/main /app/main
COPY pyvolt /app/main/src/pyvolt

# Install dependencies (if any)
RUN pip install --no-cache-dir -r /app/main/requirements.txt
RUN pip install --no-cache-dir /app/main/src/pyvolt/.

# Set the default command to run the script
CMD ["python", "/app/main/main.py"]