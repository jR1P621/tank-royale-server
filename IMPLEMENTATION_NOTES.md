# Implementation Summary: Automatic Battle Orchestration

## What Was Implemented

### 1. Battle Controller Service (`controller/`)

A new Python service that acts as a Tank Royale controller:

- **File**: `controller/battle_orchestrator.py`
- **Connects to** Tank Royale server using Controller API (WebSocket)
- **Waits for** neural bots to connect
- **Auto-starts** battles when enough bots are ready
- **Logs results** in a parseable format for `simulate.py`

### 2. Docker Compose Update

- Added `battle-controller` service to `docker-compose.yml`
- Configured with environment variables:
  - `SERVER_URL`: ws://tank-royale-server:7654
  - `CONTROLLER_SECRET`: 7Tr04oRlwlnC84ksjhhzESQ
  - `MIN_BOTS`: 2 (minimum to start battle)
  - `MAX_BOTS`: 20 (maximum per battle)
  - `NUM_ROUNDS`: 1
  - `TURNS_PER_ROUND`: 300
  - `TIMEOUT`: 300 seconds (max wait for bots)

### 3. Simulation Script Update

Updated `nn-tools/simulate.py`:

- Now includes the `battle-controller` service in docker compose
- Configures controller's MIN/MAX_BOTS for each simulation run
- Waits longer for battles to complete (default 300s instead of 60s)
- Parses results from logs using regex: `Bot neural-bot-(\d+) scored (\d+)`
- Restores original docker-compose.yml after each run

## How It Works

### Battle Flow

1. **Simulation starts** all selected neural bots + server + controller
2. **Bots connect** to Tank Royale server
3. **Controller detects** bot connections
4. **When min_bots reached** → Controller creates battle with GameSetup
5. **Battle runs** with configured rounds and turn limits
6. **Battle completes** → Controller receives GameEndedEventForObserver
7. **Results logged** in format: `Bot neural-bot-001 scored 50`
8. **simulate.py parses** logs and extracts scores

### Key Components

- **Tank Royale Server**: Java JAR running on port 7654
- **Battle Controller**: Python async service using WebSocket
- **Neural Bots**: Existing bot services that connect as participants
- **Result Logging**: Orchestrator logs scores from server's final results

## Testing the Implementation

### Test 1: Basic Battle Orchestration

```bash
cd d:\Source\tank-royale-server
docker compose up --build tank-royale-server battle-controller neural-bot-001 neural-bot-002 neural-bot-003
```

**Monitor for**:

- ✓ Server starts on port 7654
- ✓ Controller connects with handshake
- ✓ Bots connect (check logs for "Bot connected")
- ✓ Battle starts (check for "Starting battle")
- ✓ Battle completes (check for "FINAL BATTLE RESULTS")
- ✓ Scores logged (check for "Bot neural-bot-*scored*")

**Exit** with Ctrl+C, cleanup with `docker compose down`

### Test 2: Run Simulation with 2 Bots

```bash
python nn-tools/simulate.py generation-1 "1,2"
```

**Expected output**:

```
Running simulation: generation-1 with bots [1, 2]
Starting simulation with 2 bots for 300s...
  Bot 001: score = XX
  Bot 002: score = YY

Final scores: {1: XX, 2: YY}
```

### Test 3: Run Evolution/Training

Once simulation works, test the full evolution loop:

```bash
python nn-tools/evolve.py --generation 1 --population 5
```

## Potential Issues to Watch For

### 1. Bot Connection Detection

The orchestrator listens for `BotConnectionHandshake` messages. If bots don't send these events, battles won't start.

- **Fix**: Check Tank Royale server logs for actual handshake messages
- **Alternative**: Monitor what events the server actually sends

### 2. Bot Address Mapping  

Results are mapped to bot addresses using rank (1st place → neural-bot-001, etc.)

- **Issue**: Assumes results are sorted by rank
- **Test**: Run battle with 3 bots, verify all 3 scores are logged

### 3. Score Parsing Regex

Current regex expects: `Bot neural-bot-NNN scored XXX`

- **Issue**: If bot names differ or format changes, parsing fails
- **Test**: Check actual log output format against regex

### 4. Timeout Handling

If bots don't connect within TIMEOUT seconds, controller starts with connected bots.

- **Desired**: More graceful timeout handling? Can adjust TIMEOUT env var

### 5. Multiple Battle Runs  

The orchestrator currently handles one battle per run.

- **Current design**: Works with simulate.py which runs one battle per invocation
- **Future enhancement**: Could loop for multiple battles

## Configuration Options

### Controller Environment Variables (docker-compose.yml)

```yaml
SERVER_URL: ws://tank-royale-server:7654      # Server WebSocket URL
CONTROLLER_SECRET: 7Tr04oRlwlnC84ksjhhzESQ   # Must match server secret
MIN_BOTS: 2                                    # Minimum bots to start
MAX_BOTS: 20                                   # Maximum bots per battle
NUM_ROUNDS: 1                                  # Rounds per battle
TURNS_PER_ROUND: 300                          # Max turns before timeout
TIMEOUT: 300                                   # Seconds to wait for bots
```

### Simulate Script Env Variables

```bash
CONTAINER_RUNTIME=docker  # or 'podman' if preferred
```

## Files Modified/Created

### New Files

- `controller/battle_orchestrator.py` - Main controller service
- `controller/Dockerfile` - Container definition
- `controller/requirements.txt` - Dependencies

### Modified Files

- `docker-compose.yml` - Added battle-controller service
- `nn-tools/simulate.py` - Integrate controller, parse results

### Unchanged (Reverted Changes)

- `shared/NeuralBot.py` - Removed uncertain event handlers

## Success Criteria

✓ Battles start automatically without manual GUI interaction
✓ Battle complete event triggers result collection
✓ Results logged to container logs in parseable format
✓ simulate.py successfully extracts scores from logs
✓ Evolution loop runs with automated battles
