# Quick Reference: Tank Royale Battle Control

## TL;DR - Key Findings

| Question | Answer |
|----------|--------|
| **Is there a Controller/GameRunner class?** | ❌ **NO** - Must build your own |
| **Can I start battles programmatically?** | ✅ Yes, but via WebSocket messages |
| **What library do I use?** | `websockets` (not included in package) |
| **Can I configure game rules?** | ✅ Yes, via `GameSetup` class |
| **Can I get battle results?** | ✅ Yes, in `GameEndedEventForObserver` |
| **Can I monitor battle progress?** | ✅ Yes, via event stream |
| **Is it async or sync?** | 🔷 Async only - wrap for sync |

---

## Minimal Working Example

```python
import asyncio
import json
import websockets
from dataclasses import asdict
from robocode_tank_royale.schema import (
    Message, ControllerHandshake, StartGame, GameSetup, BotAddress, StopGame
)

async def run_battle():
    # 1. Connect
    ws = await websockets.connect("ws://tank-royale-server:7654")
    
    # 2. Handshake
    handshake = ControllerHandshake(
        session_id="test",
        name="Controller",
        version="1.0",
        type=Message.Type.CONTROLLER_HANDSHAKE,
        secret="j1etPtYUMVuCWGUlW6hF6AV"
    )
    await ws.send(json.dumps(asdict(handshake)))
    
    # 3. Receive server config
    msg = await ws.recv()
    print(f"Server says: {json.loads(msg)['type']}")
    
    # 4. Start battle
    game_setup = GameSetup(
        game_type="melee",
        arena_width=800, arena_height=600,
        min_number_of_participants=2,
        max_number_of_participants=10,
        number_of_rounds=3,
        gun_cooling_rate=0.1,
        max_inactivity_turns=50,
        turn_timeout=30000, ready_timeout=10000,
        default_turns_per_second=30,
        is_arena_width_locked=False,
        is_arena_height_locked=False,
        is_min_number_of_participants_locked=False,
        is_max_number_of_participants_locked=False,
        is_number_of_rounds_locked=False,
        is_gun_cooling_rate_locked=False,
        is_max_inactivity_turns_locked=False,
        is_turn_timeout_locked=False,
        is_ready_timeout_locked=False,
    )
    
    start = StartGame(
        bot_addresses=[
            BotAddress("bot-1", 9001),
            BotAddress("bot-2", 9001),
        ],
        game_setup=game_setup,
        type=Message.Type.START_GAME
    )
    await ws.send(json.dumps(asdict(start)))
    
    # 5. Listen for events
    while True:
        msg = json.loads(await ws.recv())
        if msg['type'] == 'GameEndedEventForObserver':
            print("Game over!")
            print(msg['results'])
            break
    
    # 6. Stop
    await ws.send(json.dumps(asdict(
        StopGame(type=Message.Type.STOP_GAME)
    )))
    await ws.close()

asyncio.run(run_battle())
```

---

## Classes You Need (from robocode_tank_royale.schema)

### Commands (You Send)

- `StartGame(bot_addresses, game_setup, type)`
- `StopGame(type)`
- `PauseGame(type)`
- `ResumeGame(type)`
- `ControllerHandshake(session_id, name, version, type, secret)`

### Config

- `GameSetup(...)` - 20 required parameters!
- `BotAddress(host, port)`

### Events (You Receive)

- `GameStartedEventForObserver` - Game started
- `RoundStartedEvent` - Round starts
- `TickEventForObserver` - Per-tick state (frequent!)
- `RoundEndedEventForObserver` - Round ends → `results`
- `GameEndedEventForObserver` - Game ends → `results`

### Results

- `ResultsForObserver` - In results arrays
  - Fields: id, name, version, rank, total_score, first_places, etc.

---

## Game Setup Parameters (All Required!)

```python
GameSetup(
    # Identity
    game_type="melee",                      # Game type
    
    # Arena
    arena_width=800,                        # Pixels
    arena_height=600,                       # Pixels
    
    # Participants
    min_number_of_participants=1,
    max_number_of_participants=10,
    
    # Duration
    number_of_rounds=3,                     # How many rounds
    
    # Physics
    gun_cooling_rate=0.1,
    max_inactivity_turns=50,
    
    # Timing (milliseconds)
    turn_timeout=30000,                     # 30 seconds per turn
    ready_timeout=10000,                    # 10 seconds for bots to ready
    
    # Speed
    default_turns_per_second=30,            # TPS (game speed)
    
    # Lock flags (all required as bool)
    is_arena_width_locked=False,
    is_arena_height_locked=False,
    is_min_number_of_participants_locked=False,
    is_max_number_of_participants_locked=False,
    is_number_of_rounds_locked=False,
    is_gun_cooling_rate_locked=False,
    is_max_inactivity_turns_locked=False,
    is_turn_timeout_locked=False,
    is_ready_timeout_locked=False,
)
```

---

## WebSocket Flow (ASCII)

```
You                          Tank Royale Server

CONNECT ─────────────────────►
                              
SEND Handshake ──────────────►
      
                   ◄────────── ServerHandshake
                              
SEND StartGame ───────────────►
                              
                   ◄────────── GameStartedEventForObserver
                              
                   ◄────────── RoundStartedEvent
                              
                   ◄────────── TickEventForObserver (tick 1)
                              
                   ◄────────── TickEventForObserver (tick 2)
                              
                   ◄────────── ... (many ticks)
                              
                   ◄────────── RoundEndedEventForObserver
                              
                   ◄────────── RoundStartedEvent (next round)
                              
                   ◄────────── ... (repeat for each round)
                              
                   ◄────────── GameEndedEventForObserver
                              
SEND StopGame ─────────────────►
                              
CLOSE ─────────────────────────►
```

---

## Message Type Enum Values

```python
Message.Type.CONTROLLER_HANDSHAKE
Message.Type.START_GAME
Message.Type.STOP_GAME
Message.Type.PAUSE_GAME
Message.Type.RESUME_GAME
Message.Type.CHANGE_TPS

Message.Type.SERVER_HANDSHAKE
Message.Type.GAME_STARTED_EVENT_FOR_OBSERVER
Message.Type.GAME_ENDED_EVENT_FOR_OBSERVER
Message.Type.GAME_ABORTED_EVENT
Message.Type.GAME_PAUSED_EVENT_FOR_OBSERVER
Message.Type.GAME_RESUMED_EVENT_FOR_OBSERVER
Message.Type.ROUND_STARTED_EVENT
Message.Type.ROUND_ENDED_EVENT_FOR_OBSERVER
Message.Type.TICK_EVENT_FOR_OBSERVER
Message.Type.TPS_CHANGED_EVENT
Message.Type.BOT_LIST_UPDATE

# ... and 23 more types
```

---

## JSON Message Examples

### ControllerHandshake (you send)

```json
{
  "type": "ControllerHandshake",
  "session_id": "my-session",
  "name": "MyController",
  "version": "1.0",
  "secret": "server-secret"
}
```

### StartGame (you send)

```json
{
  "type": "StartGame",
  "bot_addresses": [
    {"host": "bot-1", "port": 9001},
    {"host": "bot-2", "port": 9001}
  ],
  "game_setup": {
    "game_type": "melee",
    "arena_width": 800,
    ...all 20 fields...
  }
}
```

### GameEndedEventForObserver (server sends)

```json
{
  "type": "GameEndedEventForObserver",
  "number_of_rounds": 3,
  "results": [
    {
      "id": 1,
      "name": "Bot1",
      "rank": 1,
      "total_score": 500
    },
    {
      "id": 2,
      "name": "Bot2",
      "rank": 2,
      "total_score": 350
    }
  ]
}
```

---

## Imports Needed

```python
import asyncio
import json
import websockets
from dataclasses import asdict, fields
from robocode_tank_royale.schema import (
    Message,
    ControllerHandshake, StartGame, StopGame, PauseGame, ResumeGame,
    GameSetup, BotAddress,
    GameStartedEventForObserver, GameEndedEventForObserver,
    RoundStartedEvent, RoundEndedEventForObserver,
    TickEventForObserver, ResultsForObserver,
)
```

---

## Common Gotchas

### 1. GameSetup Requires ALL 20 Fields

```python
# ❌ This will fail - missing required fields
GameSetup(game_type="melee")

# ✅ This works - all fields provided
GameSetup(
    game_type="melee",
    arena_width=800,
    is_arena_width_locked=False,
    # ... all 20 fields
)
```

### 2. Message Type Must Be Specified

```python
# ❌ This fails
StartGame(bot_addresses=[...])

# ✅ This works
StartGame(
    bot_addresses=[...],
    type=Message.Type.START_GAME
)
```

### 3. Server Can Lock Settings

```python
# Server's GameSetup might have:
is_arena_width_locked=True  # Can't override this

# So your StartGame config will be ignored for locked fields
```

### 4. Serialization Required

```python
# ❌ Can't send directly
await ws.send(start_game_object)

# ✅ Convert to dict, then JSON
await ws.send(json.dumps(asdict(start_game_object)))
```

### 5. Async Only

```python
# ❌ Can't use sync code
result = controller.start_battle(bots)

# ✅ Must use async/await or asyncio.run()
result = asyncio.run(controller.start_battle(bots))
```

---

## Performance Notes

- **TickEventForObserver**: Sent every game tick
  - At 30 TPS, that's 30 messages/second
  - 3 rounds × 450 turns = ~40,500 tick events!
  - Consider sampling or filtering in production

- **Message Size**: Each message is JSON, compact
  - Typical tick event: ~1KB
  - You can receive all messages or filter by type

---

## Recommended Next Steps

1. **Read** `RESEARCH_FINAL_REPORT.md` for complete details
2. **Study** `WEBSOCKET_PROTOCOL_REFERENCE.md` for message formats
3. **Review** `example_battle_orchestrator.py` for implementation pattern
4. **Copy** pattern and adapt for your use case
5. **Test** with actual Tank Royale server

---

## Version Info

- **Package**: robocode-tank-royale v0.36.1
- **Home**: <https://robocode-dev.github.io/tank-royale>
- **Dependencies**: websockets, PyYAML, pycountry, mypy, pip, setuptools
- **Research Date**: March 2, 2026
