# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend.py .
COPY . .

# Expose port for FastAPI
EXPOSE 8080

# Pre-download the model during build (optional, for faster startup)
RUN python -c "from transformers import AutoTokenizer, AutoModelForSeq2SeqLM; \
    AutoTokenizer.from_pretrained('google/flan-t5-small'); \
    AutoModelForSeq2SeqLM.from_pretrained('google/flan-t5-small')"

# Run the FastAPI backend
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8080"]
