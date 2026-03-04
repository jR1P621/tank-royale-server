# Quick Start: Testing Automatic Battle Orchestration

## Pre-Flight Checks ✓

- [x] docker-compose.yml is syntactically valid
- [x] controller/battle_orchestrator.py has valid Python syntax
- [x] nn-tools/simulate.py has valid Python syntax
- [x] shared/NeuralBot.py has valid Python syntax

## Step 1: Build and Test Controller Service Alone

**Goal**: Verify the battle orchestrator service builds and connects to the server

```bash
# Terminal 1: Start server + controller only
cd d:\Source\tank-royale-server
docker compose up --build tank-royale-server battle-controller

# Watch logs for:
# - "Connecting to ws://tank-royale-server:7654"
# - "✓ Connected to server successfully"
# - "Waiting for 2-20 bots to connect"
```

**Expected**: Controller starts and waits for bots (will timeout after 300s since no bots connect)

---

## Step 2: Test with Example Bots

**Goal**: Verify bots connect and battle starts automatically

```bash
# Terminal 1: Already running, or restart with bots
docker compose up --build tank-royale-server battle-controller example-bot path-bot

# Watch for:
# - "✓ Bot connected: ExampleBot"
# - "✓ Bot connected: PathBot"
# - "Starting battle with 2 bots, 1 round(s)"
# - "✓ Battle started with 2 participants"
# - "✓ Battle completed!"
# - "Bot * scored *" (result log)
```

**Expected**: Battle runs automatically without GUI interaction

---

## Step 3: Test Neural Bot Simulation

**Goal**: Verify simulate.py works with controller

```bash
# First, check that bot directories exist
ls generations/generation-1/bot-001/  # Should have Dockerfile, NeuralBot.py, NeuralBot.json, requirements.txt

# Run simulation with 2 neural bots
python .\nn-tools\simulate.py generation-1 "1,2"

# Watch for:
# - "Starting simulation with 2 bots for 300s"
# - Server, bots, and controller all start
# - Logs show battle progress
# - "FINAL BATTLE RESULTS"
# - "Bot 001: score = XX"
# - "Bot 002: score = YY"
# - "Final scores: {1: XX, 2: YY}"
# - Cleanup: containers stop and original docker-compose.yml restored
```

**Expected**: Simulation completes, returns score dictionary

---

## Step 4: Test Larger Batch

Once Step 3 works, test with more bots:

```bash
# Simulate with 5 bots
python .\nn-tools\simulate.py generation-1 "1,2,3,4,5"

# Or use the default in the script
cd nn-tools
python simulate.py
```

---

## Troubleshooting

### Issue: "No scores found in logs!"

**Cause**: Battle didn't complete or controller didn't log results

**Check**:

```bash
docker compose logs battle-controller
```

Look for error messages in controller logs.

**Solutions**:

1. Verify server started: `docker compose logs tank-royale-server`
2. Verify bots connected: Look for "Bot connected" in logs
3. Increase TIMEOUT if bots are slow to start
4. Check network connectivity between containers: `docker network ls`

### Issue: "Bot neural-bot-*scored*" doesn't appear

**Cause**: Log format doesn't match regex

**Check**: Run battle manually and grep for "scored":

```bash
docker compose up ... tank-royale-server battle-controller neural-bot-001 neural-bot-002
# In another window:
docker compose logs | grep -i "bot.*scored"
```

**Fix**: Update the regex in `nn-tools/simulate.py` if format differs

### Issue: Bots don't connect

**Cause**: Bot image not built, network issues, or authentication failure

**Check**:

```bash
docker compose up --build tank-royale-server neural-bot-001
docker compose logs neural-bot-001
```

Look for connection errors.

### Issue: Docker compose down isn't cleaning up

**Manual cleanup**:

```bash
docker compose down --remove-orphans
docker container prune
```

---

## How to Roll Back (If Needed)

The implementation adds new files/changes that are non-destructive:

```bash
# Revert simulate.py to original (keep old copy first)
git checkout nn-tools/simulate.py

# Remove controller service (edit docker-compose.yml manually or restore)
git checkout docker-compose.yml

# Remove controller directory
rd /s controller
```

---

## Success Indicators

✓ Battles start without manual GUI interaction
✓ Results are logged to console/containers
✓ simulate.py parses scores successfully
✓ Evolution scripts work with new workflow

---

## Next Steps

Once all tests pass:

1. Run a full evolution cycle:

   ```bash
   python nn-tools/evolve.py --generation 1
   ```

2. Monitor performance to ensure battles complete in timely manner

3. Adjust TIMEOUT, NUM_ROUNDS, or TURNS_PER_ROUND env vars if needed

4. Consider adding:
   - Battle result metrics (win rate, kill ratio, etc.)
   - Contest logging to separate file
   - Multiple battle runs per simulation for statistical significance
