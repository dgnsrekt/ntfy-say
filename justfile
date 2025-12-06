# Load environment variables from .env file
set dotenv-load

# Default recipe: run the service
default: run

# Build the binary
build:
    go build -o nfty-say .

# Run the service (builds first if needed)
run: build
    ./nfty-say

# Run with live reload (requires watchexec)
watch:
    watchexec -r -e go -- go run .

# Clean build artifacts
clean:
    rm -f nfty-say

# Docker recipes

# Build the Docker image
docker-build:
    docker compose build

# Start the container (detached)
docker-up:
    docker compose up -d

# Stop the container
docker-down:
    docker compose down

# View container logs
docker-logs:
    docker compose logs -f

# Rebuild and restart container
docker-restart: docker-build
    docker compose up -d --force-recreate
