#!/bin/bash

# Script to build and run the Unified Knowledge Base System using Docker

# Function to display help message
show_help() {
  echo "Usage: ./docker-run.sh [OPTIONS]"
  echo ""
  echo "Options:"
  echo "  -b, --build     Build the Docker images before starting"
  echo "  -d, --detach    Run containers in detached mode"
  echo "  -s, --stop      Stop running containers"
  echo "  -r, --restart   Restart running containers"
  echo "  -c, --clean     Stop containers and remove volumes"
  echo "  -h, --help      Show this help message"
  echo ""
}

# Parse command line arguments
BUILD=false
DETACH=""
ACTION="up"
CLEAN=""

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -b|--build)
      BUILD=true
      shift
      ;;
    -d|--detach)
      DETACH="-d"
      shift
      ;;
    -s|--stop)
      ACTION="down"
      shift
      ;;
    -r|--restart)
      ACTION="restart"
      shift
      ;;
    -c|--clean)
      ACTION="down"
      CLEAN="--volumes"
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $key"
      show_help
      exit 1
      ;;
  esac
done

# Create data directory if it doesn't exist
mkdir -p data

# Build images if requested
if [ "$BUILD" = true ]; then
  echo "Building Docker images..."
  docker-compose build
fi

# Perform the requested action
case $ACTION in
  up)
    echo "Starting containers..."
    docker-compose up $DETACH
    if [ -z "$DETACH" ]; then
      echo "Containers are running in the foreground. Press Ctrl+C to stop."
    else
      echo "Containers are running in the background."
      echo "Access the API at http://localhost:8000"
      echo "API documentation is available at http://localhost:8000/docs"
    fi
    ;;
  down)
    echo "Stopping containers..."
    docker-compose down $CLEAN
    if [ -n "$CLEAN" ]; then
      echo "Containers stopped and volumes removed."
    else
      echo "Containers stopped."
    fi
    ;;
  restart)
    echo "Restarting containers..."
    docker-compose restart
    echo "Containers restarted."
    echo "Access the API at http://localhost:8000"
    echo "API documentation is available at http://localhost:8000/docs"
    ;;
esac