#!/bin/bash

# MnemosyneOS Quickstart Setup Script
# This script will set up and run MnemosyneOS with your OpenAI API key

cat > /tmp/mnemosyneos_quickstart.sh << 'EOF'
#!/bin/bash

# MnemosyneOS Quickstart Script
set -e  # Exit on any error

# Configuration
PORT=8208
PROJECT_DIR="$HOME/mnemosyneos"
DOCKER_COMPOSE_FILE="docker-compose.standalone.yml"
ENV_FILE="$PROJECT_DIR/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Docker is installed
if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command_exists docker-compose; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.standalone.yml" ]; then
    print_warning "docker-compose.standalone.yml not found in current directory."
    read -p "Are you in the MnemosyneOS project directory? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Please run this script from the MnemosyneOS project directory."
        exit 1
    fi
fi

# Set OpenAI API key
print_status "Setting up OpenAI API key..."
if [ -n "$OPENAI_API_KEY" ]; then
    print_status "Using OPENAI_API_KEY from environment variable"
else
    # Use the provided API key
    OPENAI_API_KEY="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"
    print_status "Using the provided OpenAI API key"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file..."
    echo "OPENAI_API_KEY=$OPENAI_API_KEY" > .env
    echo "PORT=$PORT" >> .env
else
    # Update .env file with the API key
    if grep -q "OPENAI_API_KEY" .env; then
        sed -i.bak "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$OPENAI_API_KEY/" .env
    else
        echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> .env
    fi
    print_status "Updated .env file with OpenAI API key"
fi

# Make sure the .env file has secure permissions
chmod 600 .env

# Build and run the service
print_status "Building and starting MnemosyneOS service..."
docker-compose -f $DOCKER_COMPOSE_FILE up --build -d

# Wait for the service to start
print_status "Waiting for service to start (10 seconds)..."
sleep 10

# Check if the service is running
print_status "Checking if the service is running..."
if docker-compose -f $DOCKER_COMPOSE_FILE ps | grep -q "Up"; then
    print_status "Service is running!"
else
    print_error "Service failed to start. Check logs with: docker-compose -f $DOCKER_COMPOSE_FILE logs"
    exit 1
fi

# Test the health endpoint
print_status "Testing health endpoint..."
if curl -s http://localhost:$PORT/health > /dev/null; then
    print_status "Health endpoint is responding!"
else
    print_warning "Health endpoint not immediately available. Service might still be starting."
    print_status "Waiting additional 15 seconds..."
    sleep 15
    
    if curl -s http://localhost:$PORT/health > /dev/null; then
        print_status "Health endpoint is now responding!"
    else
        print_error "Health endpoint is not available. Check service logs."
        docker-compose -f $DOCKER_COMPOSE_FILE logs
        exit 1
    fi
fi

# Final information
print_status "MnemosyneOS is now running!"
echo -e "${GREEN}Service URL:${NC} http://localhost:$PORT"
echo -e "${GREEN}API Documentation:${NC} http://localhost:$PORT/docs"
echo -e "${GREEN}Health endpoint:${NC} http://localhost:$PORT/health"
echo ""
echo -e "${YELLOW}To view logs:${NC} docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
echo -e "${YELLOW}To stop the service:${NC} docker-compose -f $DOCKER_COMPOSE_FILE down"
echo -e "${YELLOW}To restart:${NC} docker-compose -f $DOCKER_COMPOSE_FILE up -d"
echo ""
print_status "Setup complete! You can now interact with MnemosyneOS at http://localhost:$PORT"

# Check if the API key is working by testing an endpoint that uses OpenAI
print_status "Testing OpenAI integration (this might take a moment)..."
if curl -s http://localhost:$PORT/health | grep -q "healthy"; then
    print_status "OpenAI integration appears to be working correctly!"
else
    print_warning "OpenAI integration test inconclusive. Please check the API docs at http://localhost:$PORT/docs to verify functionality."
fi
EOF

# Make the script executable and run it
chmod +x /tmp/mnemosyneos_quickstart.sh
echo "Starting MnemosyneOS setup..."
cd $(pwd) && /tmp/mnemosyneos_quickstart.sh