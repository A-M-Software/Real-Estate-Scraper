# syntax=docker/dockerfile:1
FROM python:3.14.0

# Define work directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Update pip & install dependencies
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt

# Copy all other files
COPY . .

# Run the bot
CMD ["python3", "run_bot.py"]
