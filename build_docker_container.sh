#!/bin/bash

rm -rf venv

# Build Dockerfile
docker build -t aurora_tracker .

# Run Docker container
docker compose up -d

python3 -m venv venv
pip install -r requirements.txt