# Use Python 3.8-slim as the base image
FROM python:3.8-slim

# Install system dependencies required for Docker CLI and git installations
# This includes necessary tools like curl, gnupg for the GPG key, and ca-certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker’s official GPG key for ensuring the downloads are valid
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the Docker stable repository for Debian packages
# This involves adding the Docker repository to the system's sources list for package installation
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list

# Install Docker CLI to enable Docker commands within the container
# This allows managing Docker containers within this container
RUN apt-get update && apt-get install -y docker-ce-cli

# Install git, allowing code management operations within the container
RUN apt-get update && apt-get install -y git

# Clean up the package lists to reduce image size
RUN apt-get clean

# Set the working directory inside the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install pipreqs, a tool to automatically generate Python project dependencies
RUN pip install --no-cache-dir pipreqs 

# Use pipreqs to generate a requirements.txt file based on imports
RUN python -m  pipreqs.pipreqs . --force

# Install Python dependencies from the generated requirements.txt file
RUN pip install --no-cache-dir -r requirements.txt

# List the contents of /app to verify the copy and file structure
RUN ls -la /app

# Command to run the application
CMD ["python", "builder.py"]
