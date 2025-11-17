#!/bin/bash

# Simple script to build and run the Column Pruning Agent in Docker

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Building Column Pruning Agent Docker image...${NC}"
docker build -f Dockerfile.column_agent -t column-pruning-agent .

echo -e "${GREEN}Build complete!${NC}"
echo ""
echo -e "${BLUE}Starting Column Pruning Agent in interactive mode...${NC}"
echo "Make sure you have set GOOGLE_API_KEY in your .env file or environment"
echo ""

# Check if .env exists
if [ -f .env ]; then
    docker run -it --rm --env-file .env column-pruning-agent
else
    echo "No .env file found. Using environment variable GOOGLE_API_KEY"
    docker run -it --rm -e GOOGLE_API_KEY="${GOOGLE_API_KEY}" column-pruning-agent
fi
