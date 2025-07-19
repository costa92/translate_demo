#!/bin/bash
# Docker deployment example for the Unified Knowledge Base System

# Build the Docker image
echo "Building Docker image..."
docker build -t unified-knowledge-base:latest .

# Run the container
echo "Running container..."
docker run -d \
  --name knowledge-base \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your-api-key" \
  -e STORAGE_PROVIDER="memory" \
  -e EMBEDDING_PROVIDER="sentence_transformers" \
  -e GENERATION_PROVIDER="openai" \
  -v $(pwd)/data:/app/data \
  unified-knowledge-base:latest

echo "Container started. API available at http://localhost:8000"
echo "API documentation available at http://localhost:8000/docs"

# Show logs
echo "Showing container logs (Ctrl+C to exit)..."
docker logs -f knowledge-base