# Use an official Python base image
FROM python:3.9-slim

# Copy the main module (nr_module) and pyvolt into the container
COPY envvarco/envvarco /app/envvarco
COPY pyvolt /app/envvarco/src/pyvolt

# Install dependencies (if any)
RUN pip install --no-cache-dir -r /app/envvarco/requirements.txt
RUN pip install --no-cache-dir /app/envvarco/src/pyvolt/.

# Set the default command to run the script
CMD ["python", "/app/envvarco/envvarco.py"]