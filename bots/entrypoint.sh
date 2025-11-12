#!/bin/bash
set -e

# List available bots
echo "Available bots:"
for dir in /app/bots/*/; do
    if [ -d "$dir" ]; then
        bot_name=$(basename "$dir")
        echo "  - $bot_name"
    fi
done
echo ""

# BOTS can be comma-separated list like "Crazy,SpinBot,Corners"
IFS=',' read -ra BOT_LIST <<< "$BOTS"

pids=()

for bot in "${BOT_LIST[@]}"; do
    bot=$(echo "$bot" | xargs)  # trim whitespace
    bot_dir="/app/bots/$bot"

    if [ -d "$bot_dir" ]; then
        echo "Starting bot: $bot"
        cd "$bot_dir"
        SERVER_URL="$SERVER_URL" SERVER_SECRET="$SERVER_SECRET" dotnet run &
        pids+=($!)
        cd /app
    else
        echo "Warning: Bot directory not found: $bot_dir"
    fi
done

# Wait for all bot processes
for pid in "${pids[@]}"; do
    wait $pid
done
