# Use an official Python runtime as a parent image
FROM python:3.10.11-slim

# Set the working directory in the container
WORKDIR /home

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir reduces image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 8501 available to the world outside this container
# Cloud Run will automatically map its internal port to this
EXPOSE 8501

# Define environment variable (Cloud Run sets this)
# Streamlit will listen on the port specified by the $PORT environment variable
ENV PORT 8501

# Run app.py when the container launches using Streamlit
# Use 0.0.0.0 to ensure it's accessible from outside the container
# server.enableCORS and enableXsrfProtection are often needed for embedding/proxying like Cloud Run
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]