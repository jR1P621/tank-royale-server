# Simulator Issues and Fixes

## Problem 1: Multiple Simulations' Results Getting Mixed (CRITICAL)

### Symptoms

- Final scores showing 40 bots instead of expected 20
- Duplicate bot IDs with different scores
- Bot 019 appearing with score 382 AND 1426 in same run

### Root Cause

The simulator was using `docker compose logs -f` which:

1. Outputs **all historical logs** from all containers, not just new logs
2. When running multiple simulations, old battle results get re-parsed
3. Score parsing was pulling results from multiple previous battles simultaneously

### Solution Applied

**nn-tools/simulate.py Changes:**

1. **Clear logs before each simulation** - Added:

   ```python
   subprocess.run(
       [CONTAINER_RUNTIME, "compose", "logs", "--tail", "0"],
       stdout=subprocess.DEVNULL,
       stderr=subprocess.DEVNULL,
   )
   ```

2. **Read only battle-controller logs** - Changed from:

   ```python
   [CONTAINER_RUNTIME, "compose", "logs", "-f"]  # All containers
   ```

   To:

   ```python
   [CONTAINER_RUNTIME, "logs", "-f", "battle-controller"]  # Only controller
   ```

3. **Improved score parsing** - Better regex pattern:

   ```python
   match = re.search(
       r"Bot\s+(?:neural-bot-|NeuralBot-)(\d+)\s+scored\s+(\d+)", line
   )
   ```

   With deduplication logic to keep highest score if duplicates exist.

4. **Better wait logic** - Increased wait time after game ends from 10s to 15s to ensure all logs are captured.

---

## Problem 2: Battles Only Running ~200 Turns (Instead of 1500-2000)

### Symptoms

- Log shows: "Round 1 progress: turn 200" then battle ends
- Only 1 round running instead of multiple
- Battles finishing too quickly

### Root Cause

**docker-compose.yml** had:

```
NUM_ROUNDS: 1
TURNS_PER_ROUND: 300 (default)
```

This limits battles to 1 × 300 = **300 turns maximum**.

### Solution Applied

Updated docker-compose.yml:

```
NUM_ROUNDS: 6  # Changed from 1
```

This gives 6 × 300 = **1800 turns per simulation** (within expected 1500-2000 range).

---

## How to Verify the Fixes

1. **Run a test simulation:**

   ```powershell
   python .\nn-tools\simulate.py
   ```

2. **Check the output for:**
   - ✓ Exactly 20 neural bots in final results (bots 001-020)
   - ✓ No duplicate bot IDs in results
   - ✓ Turn count: You should now see progress updates for turns 100, 200, 300, 400, 500, 600, etc.
   - ✓ Total turns logged should reflect multiple rounds

3. **Run multiple simulations in sequence:**

   ```powershell
   python .\nn-tools\simulate.py; python .\nn-tools\simulate.py
   ```

   Results should be completely separate with no mixing between runs.

---

## Configuration Summary

**Key Parameters in docker-compose.yml:**

- `MIN_BOTS: 30` - Requires 30 bots to start battle
- `MAX_BOTS: 30` - Maximum 30 bots per battle  
- `EXPECTED_NEURAL_BOTS: 20` - Expects 20 neural bots (generated)
- `REQUIRED_NON_NEURAL_BOTS: 10` - Requires 10 example/sample bots
- `NUM_ROUNDS: 6` - 6 rounds per battle = 1800 turns max
- `TURNS_PER_ROUND: 300` (default) - 300 turns per round inactivity timeout

---

## Files Modified

1. `nn-tools/simulate.py` - Core simulator logic
2. `docker-compose.yml` - Battle controller configuration
