# Base image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files to the working directory
COPY . .

# Install Nginx
RUN apt-get update && apt-get install -y nginx

# Remove the default Nginx configuration
RUN rm /etc/nginx/sites-enabled/default

# Copy your Nginx configuration file
COPY nginx.conf /etc/nginx/sites-enabled/

# Expose port 80 for Nginx
EXPOSE 80

# Start Nginx and the Flask application
CMD service nginx start && python main.py
