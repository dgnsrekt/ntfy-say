# Load environment variables from .env file
set dotenv-load

# Default recipe: list available commands
default:
    @just --list

# Build the binary
build:
    go build -o ntfy-say .

# Run the service (builds first if needed)
run: build
    ./ntfy-say

# Run with live reload (requires watchexec)
watch:
    watchexec -r -e go -- go run .

# Clean build artifacts
clean:
    rm -f ntfy-say

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

# Systemd user service recipes (recommended for Fedora/PipeWire)

# Install and enable the systemd user service
service-install: build
    mkdir -p ~/.config/systemd/user
    cp ~/.config/systemd/user/ntfy-say.service ~/.config/systemd/user/ntfy-say.service.bak 2>/dev/null || true
    systemctl --user daemon-reload
    systemctl --user enable ntfy-say.service

# Start the systemd service
service-start:
    systemctl --user start ntfy-say.service

# Stop the systemd service
service-stop:
    systemctl --user stop ntfy-say.service

# Restart the systemd service (rebuilds binary first)
service-restart: build
    systemctl --user restart ntfy-say.service

# View systemd service status
service-status:
    systemctl --user status ntfy-say.service

# View systemd service logs
service-logs:
    journalctl --user -u ntfy-say.service -f
