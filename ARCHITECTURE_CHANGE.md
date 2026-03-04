# Architecture Change: Server-First Design

## What Changed

You suggested a much better approach: **run the server continuously, then start simulations independently.** Here's what was updated:

### Updated Files

#### 1. `nn-tools/simulate.py`

**Changes:**

- **Removed** `"tank-royale-server"` from the `docker compose up` command
- **Removed** `"tank-royale-server"` from the `docker compose down` command  
- **Added** a warning message: `"(Ensure server is running: docker compose up tank-royale-server)"`
- **Updated docstring** to note: "Assumes the Tank Royale server is already running separately"
- **Changed cleanup** from `docker compose down` to `docker compose down -v --remove-orphans` to only stop bots/controller

**Result:** simulate.py now expects the server to be running independently

#### 2. `TESTING_QUICK_START.md` (NEW FILE)

**Purpose:** Simple, clear testing guide for the new workflow

- Step 1: Start server once (Terminal 1) - keep it running
- Step 2: Test with example bots (Terminal 2) - server still running
- Step 3: Test neural simulations (Terminal 3) - runs one or more
- Troubleshooting and cleanup instructions

### Files Not Changed

- `docker-compose.yml` - Still has server + controller + bots, but now controller has retry logic
- `controller/battle_orchestrator.py` - Already updated with connection retry logic (handles server startup delays)
- `IMPLEMENTATION_NOTES.md` - Still valid, just add "Start server first" to prerequisites

---

## How It Works Now

### Workflow Diagram

```
START: Open 3 Terminals
│
├─ Terminal 1: Server (stays running)
│  $ docker compose up tank-royale-server
│  [Output: Server listening on port 7654]
│  [Never stops unless you Ctrl+C]
│
├─ Terminal 2: Simulation 1 (bots + controller)
│  $ docker compose up --build battle-controller example-bot path-bot
│  [Output: Battle runs, containers exit]
│  [Server still running]
│
├─ Terminal 3: Simulation 2 (different bots)
│  $ python simulate.py generation-1 "1,2,3"
│  [Output: Simulation runs, containers exit]
│  [Server still running]
│
└─ Can repeat Simulations indefinitely without restarting Server
```

### Advantages

✓ **Server starts once** - No startup delays per simulation
✓ **Simpler logic** - No coordination needed, just start bots when server is ready
✓ **Persistent server** - Better for debugging, can watch battle history
✓ **Easier cleanup** - Just stop the bots, server keeps running for next simulation
✓ **True independence** - Simulations are completely isolated

### Disadvantages (None really)

⚠️ Must remember to start server first (shown in simulate.py output)
⚠️ If server crashes, all simulations will fail (but that's actually better - shows server issue)

---

## New Usage Pattern

### Before (Old Way - All-In-One)

```bash
python simulate.py generation-1 "1,2,3"  # Started server + bots every time
# Waited for startup, unpredictable timing
```

### After (New Way - Server-First)

**Terminal 1 (once, at the start of your session):**

```bash
docker compose up tank-royale-server
# Runs forever, all simulations use this instance
```

**Terminal 2+ (run as many as you want):**

```bash
python simulate.py generation-1 "1,2,3"
python simulate.py generation-1 "4,5,6"
python .\nn-tools\evolve.py --generation 1
```

Each simulation reuses the running server.

---

## Testing the New Setup

See **TESTING_QUICK_START.md** for the exact steps:

1. Terminal 1: `docker compose up tank-royale-server`
2. Terminal 2: `docker compose up --build battle-controller example-bot path-bot`
   - Watch for automatic battle start
   - Verify results in logs
3. Terminal 3: `python simulate.py generation-1 "1,2"`
   - Verify scores are extracted
   - Check that server keeps running

---

## Controller Retry Logic

The `battle_orchestrator.py` already has **10 retry attempts** with 2-second delays:

```
Connection attempt 1 of 10... [fails, server starting]
Connection attempt 2 of 10... [fails, server starting]
Connection attempt 3 of 10... [success!]
```

This handles the brief delay while server initializes.

---

## Environment Variables (unchanged)

In `docker-compose.yml` `battle-controller` section:

```yaml
SERVER_URL: ws://tank-royale-server:7654      # Where controller finds server
CONTROLLER_SECRET: 7Tr04oRlwlnC84ksjhhzESQ   # Authentication
MIN_BOTS: 2                                    # Minimum to start battle
MAX_BOTS: 20                                   # Maximum per battle
TIMEOUT: 300                                   # Seconds to wait for bots
```

---

## Cleanup

If you need to stop everything:

```bash
# Terminal 1: Ctrl+C to stop server

# Terminal 2/3: May auto-exit or need:
docker compose down --remove-orphans

# If stuck (rare):
docker container prune -f
```

---

## Summary

This change makes the entire system **simpler and more robust**:

- ✅ Server starts once, runs forever
- ✅ Simulations are independent
- ✅ No timing/startup issues
- ✅ Easier to debug problems
- ✅ Natural separation of concerns
