# Robocode Tank Royale Python Package - Complete Research Summary

## Executive Summary

The `robocode-tank-royale` Python package (v0.36.1) is designed primarily as a **Bot API** for writing individual robot agents, not for orchestrating battles. Battle control must be done via **WebSocket protocol** using message classes from the `robocode_tank_royale.schema` module.

**Key Finding**: There is **NO dedicated Controller, GameRunner, or BattleRunner class** in the Python package. You must implement your own controller by:

1. Connecting to the Tank Royale server via WebSocket
2. Sending/receiving JSON messages using schema classes
3. Handling events asynchronously or wrapping in sync code

---

## Part 1: Available Classes & Modules

### Main Packages

- `robocode_tank_royale.bot_api` - Bot implementation and events
- `robocode_tank_royale.schema` - Message classes for server communication

### Bot API Classes

| Class | Purpose |
|-------|---------|
| `Bot` | Base class for implementing bot ai/logic |
| `BotInfo` | Load bot configuration from JSON file |
| `GameSetup` | Game configuration (loaded from server) |
| `GameType` | Game type enum (melee, 1v1, etc.) |
| `BotResults` | Individual bot results after game |
| `BotState` | Current bot state (position, energy, etc.) |
| `BulletState` | Bullet position and properties |

### Key WebSocket Handler

- `robocode_tank_royale.bot_api.internal.websocket_handler.WebSocketHandler` - Async WebSocket connection manager
  - Methods: `connect()`, `disconnect()`, `receive_messages()`, `process_message()`
  - Event handlers for: game_started, game_ended, round_started, round_ended, tick, skipped_turn

---

## Part 2: Battle Control Message Classes (Schema)

### Commands YOU Send to Server

#### 1. **StartGame** - Begin a new battle

```python
StartGame(
    bot_addresses: list[BotAddress],  # Required: which bots to include
    type: Message.Type.START_GAME,    # Required
    game_setup: GameSetup = None      # Optional: custom config or use server defaults
)
```

**BotAddress** - Identifies a bot:

- `host: str` - e.g., "localhost" or container name
- `port: int` - e.g., 9001

#### 2. **GameSetup** - Game configuration (REQUIRED for StartGame)

All parameters are required and must include lock flags:

**Required Parameters:**

- `game_type: str` - e.g., "melee", "1v1"
- `arena_width: int` - Battle arena width
- `arena_height: int` - Battle arena height
- `min_number_of_participants: int` - Minimum bots
- `max_number_of_participants: int` - Maximum bots
- `number_of_rounds: int` - Rounds to play
- `gun_cooling_rate: float` - Gun overheating recovery rate
- `max_inactivity_turns: int` - Max turns without movement/fire
- `turn_timeout: int` - Milliseconds per game turn
- `ready_timeout: int` - Milliseconds to wait for bots to ready
- `default_turns_per_second: int` - Game speed (TPS)

**Lock Flags (all required as bool):**

- `is_arena_width_locked`
- `is_arena_height_locked`
- `is_min_number_of_participants_locked`
- `is_max_number_of_participants_locked`
- `is_number_of_rounds_locked`
- `is_gun_cooling_rate_locked`
- `is_max_inactivity_turns_locked`
- `is_turn_timeout_locked`
- `is_ready_timeout_locked`

⚠️ **GOTCHA**: If a field is locked on the server, you cannot change it from defaults. `is_*_locked` flags typically = `False` unless server enforces restrictions.

#### 3. **StopGame** - Stop/reset the game

```python
StopGame(type: Message.Type.STOP_GAME)
```

#### 4. **PauseGame** - Pause execution

```python
PauseGame(type: Message.Type.PAUSE_GAME)
```

#### 5. **ResumeGame** - Resume from pause

```python
ResumeGame(type: Message.Type.RESUME_GAME)
```

#### 6. **ControllerHandshake** - Initial connection

```python
ControllerHandshake(
    session_id: str,              # Unique session ID
    name: str,                    # Controller name
    version: str,                 # Controller version
    type: Message.Type.CONTROLLER_HANDSHAKE,
    author: str = None,           # Optional
    secret: str = None            # Server secret if auth required
)
```

### Events YOU Receive from Server

| Event | When | Contains |
|-------|------|----------|
| `ServerHandshake` | On connection | Server config and game setup |
| `GameStartedEventForObserver` | Game starts | Participants list, game setup |
| `RoundStartedEvent` | Each round begins | Round number |
| `TickEventForObserver` | Each game tick | Current bot positions, bullet states |
| `RoundEndedEventForObserver` | Round ends | Per-round results for all bots |
| `GameEndedEventForObserver` | Game complete | Final results for all bots |
| `GamePausedEventForObserver` | Game paused | - |
| `GameResumedEventForObserver` | Resumed | - |
| `GameAbortedEvent` | Aborted | - |
| `TpsChangedEvent` | TPS adjusted | New TPS value |

### Results Classes

#### **ResultsForObserver** - Per-bot game results

```python
ResultsForObserver(
    id: int,                  # Bot ID
    name: str,                # Bot name
    version: str,             # Bot version
    rank: int,                # 1st, 2nd, 3rd, etc.
    survival: int,            # Points for survival
    last_survivor_bonus: int, # Bonus if last alive
    bullet_damage: int,       # Damage dealt by bullets
    bullet_kill_bonus: int,   # Bonus for bullet kills
    ram_damage: int,          # Damage from ramming
    ram_kill_bonus: int,      # Bonus for ram kills
    total_score: int,         # Total points
    first_places: int,        # Number of 1st place finishes
    second_places: int,       # Number of 2nd place finishes
    third_places: int,        # Number of 3rd place finishes
)
```

---

## Part 3: WebSocket Protocol Flow

### Complete Conversation Sequence

```
1. CONNECT to WebSocket
   ws://tank-royale-server:7654

2. SEND ControllerHandshake
   {
     "type": "ControllerHandshake",
     "session_id": "my-session-123",
     "name": "MyController",
     "version": "1.0",
     "secret": "j1etPtYUMVuCWGUlW6hF6AV"
   }

3. RECEIVE ServerHandshake
   {
     "type": "ServerHandshake",
     "game_setup": { ... GameSetup ... },
     "server_secret": "..."
   }

4. SEND StartGame
   {
     "type": "StartGame",
     "bot_addresses": [
       {"host": "neural-bot-001", "port": 9001},
       {"host": "neural-bot-002", "port": 9001}
     ],
     "game_setup": { ... GameSetup ... }
   }

5. RECEIVE GameStartedEventForObserver
   {
     "type": "GameStartedEventForObserver",
     "game_setup": { ... },
     "participants": [
       {"id": 1, "name": "Bot1", ...},
       {"id": 2, "name": "Bot2", ...}
     ]
   }

6. RECEIVE RoundStartedEvent
   {"type": "RoundStartedEvent", "round_number": 1}

7. RECEIVE TickEventForObserver (multiple times per round)
   {"type": "TickEventForObserver", "turn": 1, "bots": [...], "bullets": [...]}

8. RECEIVE RoundEndedEventForObserver
   {
     "type": "RoundEndedEventForObserver",
     "round_number": 1,
     "results": [ResultsForObserver, ...]
   }

9. (Repeat 6-8 for each round)

10. RECEIVE GameEndedEventForObserver
    {
      "type": "GameEndedEventForObserver",
      "number_of_rounds": 3,
      "results": [ResultsForObserver, ...]
    }

11. SEND StopGame
    {"type": "StopGame"}

12. (Optional) SEND new StartGame for next battle
```

---

## Part 4: Available Message Types (Message.Type Enum)

### Commands to Server

- `START_GAME`
- `STOP_GAME`
- `PAUSE_GAME`
- `RESUME_GAME`
- `CONTROLLER_HANDSHAKE`
- `OBSERVER_HANDSHAKE`
- `CHANGE_TPS`

### Events from Server

- `GAME_STARTED_EVENT_FOR_OBSERVER`
- `GAME_ENDED_EVENT_FOR_OBSERVER`
- `GAME_PAUSED_EVENT_FOR_OBSERVER`
- `GAME_RESUMED_EVENT_FOR_OBSERVER`
- `GAME_ABORTED_EVENT`
- `ROUND_STARTED_EVENT`
- `ROUND_ENDED_EVENT_FOR_OBSERVER`
- `TICK_EVENT_FOR_OBSERVER`
- `TPS_CHANGED_EVENT`
- `SERVER_HANDSHAKE`
- `BOT_LIST_UPDATE`

---

## Part 5: Best Practices for Implementation

### Serialization

```python
from dataclasses import asdict
import json

# Convert schema object to JSON for sending
message_dict = asdict(my_message)
json_string = json.dumps(message_dict)

# Receive JSON and convert to object
received_dict = json.loads(json_string)
event = GameEndedEventForObserver(
    number_of_rounds=received_dict['number_of_rounds'],
    results=[ResultsForObserver(**r) for r in received_dict['results']],
    type=Message.Type.GAME_ENDED_EVENT_FOR_OBSERVER
)
```

### Async vs Sync

- **Default**: WebSocket operations are async (using `asyncio` and `websockets`)
- **For sync code**: Wrap in `asyncio.run()` or use `threading` + asyncio bridge
- **Recommendation**: Use async/await if possible for cleaner code

### Error Handling

- Always set `secret` parameter when server requires authentication
- Validate GameSetup lock flags against server capabilities
- Handle `GameAbortedEvent` for unexpected terminations
- Implement timeout logic for long-running games

---

## Part 6: Limitations & Gotchas

| Issue | Details | Workaround |
|-------|---------|-----------|
| No Controller class | Python package is Bot-only | Build custom wrapper around WebSocket |
| GameSetup complexity | All 19 fields required, including lock flags | Create helper function with defaults |
| Async-only WebSocket | Default implementation is async | Use `asyncio.run()` for sync code |
| No json methods | Must use `dataclasses.asdict()` | Create utility module for serialization |
| Event-driven design | No polling/request-response | Implement event queue/listener pattern |
| Lock flags enforcement | Server may reject changes to locked fields | Check server response for validation errors |

---

## Part 7: Summary

### ✅ What's Available

1. **Full game configuration** via `GameSetup` class
   - 11 game parameters + 9 lock flags
   - Covers rounds, TPS, timeouts, arena size, etc.

2. **Game lifecycle control**
   - StartGame → RoundStartedEvent → TickEventForObserver → RoundEndedEventForObserver → GameEndedEventForObserver → StopGame

3. **Event-based architecture**
   - 13 different event types for observers
   - Per-bot scoring and results

4. **Game control during execution**
   - PauseGame / ResumeGame
   - ChangeTps

### ❌ What's NOT Available

1. **No BattleController or GameRunner class** in Python package
2. **No sync wrapper** for WebSocket communication
3. **No built-in event listener** system (must implement manually)
4. **No bot-level callbacks** (observer perspective only)

### 🎯 Recommended Approach

**Best**: Create a thin async wrapper

- Handle handshake
- Send StartGame with BotAddress list
- Collect events in a queue
- Return results when GameEndedEventForObserver received

**Alternative**: Use `robocode_tank_royale.bot_api.internal.websocket_handler.WebSocketHandler` directly

- More low-level control
- Complex event handler passing

---

## Part 8: Quick Reference

### To start a battle

```python
from robocode_tank_royale.schema import (
    StartGame, GameSetup, BotAddress, Message
)

game_config = GameSetup(
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

bot_list = [
    BotAddress("bot-1", 9001),
    BotAddress("bot-2", 9001),
]

start_msg = StartGame(
    bot_addresses=bot_list,
    game_setup=game_config,
    type=Message.Type.START_GAME
)
```

then send `start_msg` via WebSocket as JSON.
