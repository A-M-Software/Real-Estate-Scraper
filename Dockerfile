# syntax=docker/dockerfile:1
FROM python:3.14.0

RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# uk_UA UTF-8/uk_UA UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

# Define work directory
WORKDIR /

# Set volumes for logs & data
VOLUME /logs
VOLUME /data

# Copy requirements
COPY requirements.txt requirements.txt

# Update pip & install dependencies
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt

# Copy all other files
COPY . .

# Run the script
CMD ["python3", "run.py"]
