# Use Alpine Linux as base image
FROM alpine:latest

# Install Python
RUN apk add --update --no-cache python3 py3-pip
RUN python3 -m pip install --no-cache --break-system-packages --upgrade pip setuptools

# Install supercronic - a cron replacement designed for containers
# Using build arguments allows easy version updates and multi-architecture support
ARG SUPERCRONIC_VERSION=0.2.43
ARG TARGETARCH
# Download the supercronic binary for the target architecture and make it executable
RUN wget -q "https://github.com/aptible/supercronic/releases/download/v${SUPERCRONIC_VERSION}/supercronic-linux-${TARGETARCH}" -O /usr/local/bin/supercronic && chmod +x /usr/local/bin/supercronic

# Copy the requirements file and install Python dependencies
COPY requirements.txt .

# Install dependencies
RUN python3 -m pip install --break-system-packages -r requirements.txt

# Copy the crontab into place
COPY crontab /etc/crontab

# Copy other files
COPY . .

# Run cron, and tail the primary cron log
CMD ["supercronic", "/etc/crontab"]
