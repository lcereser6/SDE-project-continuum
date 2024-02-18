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

# Install git
RUN apt-get update && apt-get install -y git && apt-get clean

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir pipreqs 
RUN python -m  pipreqs.pipreqs . --force
RUN pip install --no-cache-dir -r requirements.txt
RUN ls -la /app  # This will list the contents of /app

CMD ["python", "builder.py"]
