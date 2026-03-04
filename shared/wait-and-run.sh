#!/bin/bash
set -e

# Wait for tank-royale-server to be accessible
max_attempts=30
attempt=0

echo "Waiting for Tank Royale server at $SERVER_URL..."

while [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))
    
    # Try to connect to the server (using nc or timeout if available)
    if timeout 2 bash -c "echo > /dev/tcp/tank-royale-server/7654" 2>/dev/null; then
        echo "✓ Tank Royale server is ready!"
        break
    fi
    
    if [ $attempt -lt $max_attempts ]; then
        echo "  Attempt $attempt/$max_attempts - server not ready, waiting..."
        sleep 1
    fi
done

if [ $attempt -eq $max_attempts ]; then
    echo "⚠ Warning: Server may not be fully ready, but attempting to connect anyway..."
fi

# Wait an additional 2 seconds for the server to be fully initialized
sleep 2

# Run the bot with proper environment variables
echo "Starting bot..."
exec "$@"
