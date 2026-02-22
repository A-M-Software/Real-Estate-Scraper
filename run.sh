#!/bin/bash
# Build & run Docker container with mounted volumes for logs and data
docker build -t scraper .
docker run -v $(pwd)/logs:/logs -v $(pwd)/data:/data scraper
