# Quick Start: Testing Automatic Battle Orchestration

## Architecture: Server Runs Continuously

The Tank Royale server runs **indefinitely and independently**. Simulations start/stop only their bots and controller.

```
Terminal 1: docker compose up tank-royale-server
            (Runs forever, keep open)
                    ↓
Terminal 2: docker compose up battle-controller example-bot path-bot
            (Runs one simulation, exits)
                    ↓
Terminal 3: python simulate.py generation-1 "1,2,3"
            (Runs next simulation, exits)
                    ↓
            (Repeat as needed, server still running)
```

---

## Step 1: Start the Server Once (Terminal 1)

```bash
cd d:\Source\tank-royale-server
docker compose up tank-royale-server
```

**Expected Output:**

```
tank-royale-server | 2026-03-03 08:00:00 - INFO - Server started on port 7654
tank-royale-server | Tank Royale Server v0.34.1
... (server logs continue)
```

**⚠️ Keep this terminal open** - server must stay running for all simulations.

---

## Step 2: Test with Example Bots (Terminal 2)

While server runs in Terminal 1, open a new terminal:

```bash
cd d:\Source\tank-royale-server
docker compose up --build battle-controller example-bot path-bot
```

**Watch for:**

- ✓ "✓ Bot connected: ExampleBot"
- ✓ "✓ Bot connected: PathBot"
- ✓ "Starting battle with 2 bots"
- ✓ "✓ Battle started with 2 participants"
- ✓ "FINAL BATTLE RESULTS"
- ✓ "Bot *scored*"

**Expected:** Battle runs automatically, containers exit cleanly. Server in Terminal 1 still running.

---

## Step 2.5: Start Persistent Non-Neural Bots (Optional, Terminal 2)

If you want each neural simulation battle to include randomly selected non-neural bots, start them once and keep them running:

```bash
cd d:\Source\tank-royale-server
python .\nn-tools\start_non_neural_bots.py start
```

Check status:

```bash
python .\nn-tools\start_non_neural_bots.py status
```

---

## Step 3: Test Neural Bot Simulation (Terminal 3)

While server still runs in Terminal 1, open another terminal:

```bash
cd d:\Source\tank-royale-server

# First verify bot directories exist
ls generations/generation-1/bot-001/

# Run simulation with 2 bots
python .\nn-tools\simulate.py generation-1 "1,2"
```

**Expected Output:**

```
Running simulation: generation-1 with bots [1, 2]
Starting simulation with 2 bots for 300s...
(Ensure server is running: docker compose up tank-royale-server)
... [battle logs] ...
FINAL BATTLE RESULTS
Bot neural-bot-001 scored 50
Bot neural-bot-002 scored 45

Simulation completed in 45.3s
  Bot 001: score = 50
  Bot 002: score = 45

Final scores: {1: 50, 2: 45}
```

When non-neural bot services are running, the controller waits for all requested neural bots plus 10 non-neural bot instances (not containers) before starting each battle; `sample-bots` can contribute multiple instances.

**Success:** Bots and controller stop. Server in Terminal 1 still running.

---

## Step 4: Run More Simulations (Still in Terminal 3)

```bash
# Test with 5 bots
python .\nn-tools\simulate.py generation-1 "1,2,3,4,5"

# Test evolution (runs multiple simulations automatically)
python .\nn-tools\evolve.py --generation 1
```

Server keeps running throughout. Each simulation cleans up its bots/controller.

---

## Cleanup

### Option A: Keep server running

Just close Terminals 2 and 3. Leave Terminal 1 open for future simulations.

### Option B: Stop everything

In Terminal 1: Press `Ctrl+C`

### Option C: Force cleanup (if stuck)

```bash
docker compose down --remove-orphans
docker container prune -f
```

---

## Troubleshooting

### Server doesn't start

```bash
# Check if port 7654 is in use
docker ps | grep 7654

# Kill any existing server
docker compose down tank-royale-server

# Try again
docker compose up tank-royale-server
```

### Controller can't connect to server

```bash
# Check server is actually running
docker compose logs tank-royale-server | grep -i "started\|port"

# Monitor controller connection attempts
docker compose logs battle-controller
```

Should see "Connection attempt 1 of 10" and then success once retries work.

### No scores in simulation output

```bash
# Check full logs while simulation runs
docker compose logs | grep -E "scored|BATTLE|error"
```

Verify:

1. Server is running (Terminal 1)
2. Bots connected (look for "Bot connected" in logs)
3. Battle completed (look for "FINAL BATTLE RESULTS")

### Bots won't connect

```bash
docker compose logs neural-bot-001

# Check bot can reach server hostname
docker exec neural-bot-001 ping tank-royale-server
```

---

## Success Checklist

✓ Server starts and stays running (Terminal 1)
✓ Example bots battle automatically (Terminal 2)
✓ Neural bot simulation returns scores (Terminal 3)
✓ Multiple simulations can run sequentially
✓ Server survives all cleanup

---

## Configuration (if needed)

**Adjust simulation parameters** in `docker-compose.yml` `battle-controller` section:

```yaml
MIN_BOTS: 2           # Minimum bots required to start
MAX_BOTS: 20          # Maximum bots per battle
TIMEOUT: 300          # Seconds to wait for bots to connect
NUM_ROUNDS: 1         # Rounds per battle
TURNS_PER_ROUND: 300  # Max turns before round ends
```

Or set via environment when running:

```bash
export MIN_BOTS=2
export TIMEOUT=60
python .\nn-tools\simulate.py generation-1 "1,2"
```

---

## Next: Full Evolution Run

Once testing passes:

```bash
# Terminal 1 (keep going): docker compose up tank-royale-server

# Terminal 3: Run evolution for multiple generations
python .\nn-tools\evolve.py --generation 1 --population 20
```

This will automatically run multiple simulations, breed bots, and generate new generations.
