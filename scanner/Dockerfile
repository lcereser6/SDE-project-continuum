FROM python:3.8-slim

# Install system dependencies required for Docker CLI installation
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker’s official GPG key
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the Docker stable repository
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list

# Install Docker CLI
RUN apt-get update && apt-get install -y docker-ce-cli

# Install grype
RUN curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

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

CMD ["python", "scanner.py"]
