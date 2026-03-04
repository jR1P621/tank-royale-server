FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy controller code
COPY battle_orchestrator.py .

# Run the battle orchestrator
CMD ["python", "battle_orchestrator.py"]
