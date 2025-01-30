FROM python:3.9-slim

# Install required packages
RUN pip install --no-cache-dir google-cloud-storage google-cloud-firestore Flask requests pillow flask-cors

# Create and set working directory
WORKDIR /app

# Copy both the Python script and the credentials file
COPY image_handler.py /app/
COPY dcsc-project-440602-9412462c618e.json /app/

# Set proper permissions for the credentials file
RUN chmod 600 /app/dcsc-project-440602-9412462c618e.json

# Expose the port your app runs on
EXPOSE 5000

# Run the application
ENTRYPOINT ["python", "-u", "image_handler.py"]