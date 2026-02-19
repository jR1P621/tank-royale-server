import subprocess
import time
import os
import re
import re

def run_simulation(bot_ids, generation_dir):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    compose_file = os.path.join(script_dir, '..', 'docker-compose.yml')
    # Update docker-compose.yml to include only selected bots
    with open(compose_file, 'r') as f:
        content = f.read()
    
    # Remove existing neural-bot services
    content = re.sub(r'  neural-bot-\d+:\n.*?(?=\n\n|\n  [a-z]|\Z)', '', content, flags=re.DOTALL)
    
    # Add selected bots
    services = ""
    for bid in bot_ids:
        services += f"""
  neural-bot-{bid:03d}:
    build:
      context: ./{generation_dir}/bot-{bid:03d}
      dockerfile: Dockerfile
    container_name: neural-bot-{bid:03d}
    environment:
      SERVER_URL: ws://tank-royale-server:7654
      SERVER_SECRET: bot-secret-change-me
    depends_on:
      - tank-royale-server
    restart: unless-stopped
"""
    # Insert before the end
    content = content.rstrip() + services + "\n"
    
    with open(compose_file, 'w') as f:
        f.write(content)
    
    # Run docker compose
    subprocess.run(['docker', 'compose', 'up', '--build', '-d'] + [f'neural-bot-{bid:03d}' for bid in bot_ids] + ['tank-royale-server'], cwd='..')
    time.sleep(60)  # Wait for games
    result = subprocess.run(['docker', 'compose', 'logs'], capture_output=True, text=True, cwd='..')
    logs = result.stdout
    
    # Parse scores, assume format "Bot NeuralBot-001 scored 50"
    scores = {}
    for line in logs.split('\n'):
        match = re.search(r'Bot NeuralBot-(\d+) scored (\d+)', line)
        if match:
            bid = int(match.group(1))
            score = int(match.group(2))
            scores[bid] = score
    
    # Stop
    subprocess.run(['docker', 'compose', 'down'], cwd='..')
    
    return scores

if __name__ == "__main__":
    # Example
    bot_ids = [1,2,3,4,5]  # Select 5 bots
    scores = run_simulation(bot_ids, 'generation-1')
    print(scores)