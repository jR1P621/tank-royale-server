# robocode-tank-royale Package Research - Final Report

**Research Date**: March 2, 2026  
**Package**: robocode-tank-royale v0.36.1  
**Location**: <https://github.com/robocode-dev/tank-royale>

---

## Executive Summary

The `robocode-tank-royale` Python package is primarily a **Bot API** for writing individual robot agents. It does **NOT** include controller/orchestration classes for managing battles.

**Battle control must be implemented by you** using the message classes in `robocode_tank_royale.schema` over WebSocket.

---

## 1. AVAILABLE CONTROLLER/BATTLE MANAGEMENT CLASSES

### Direct Answer: NONE

There are **zero** battle controller/game runner classes in the Python package. This includes:

- ❌ No `Controller` class
- ❌ No `GameRunner` class
- ❌ No `BattleRunner` class
- ❌ No `BattleOrchestrator` class
- ❌ No `GameManager` class

### What IS Available Instead

**Message Classes** (in `robocode_tank_royale.schema`):

- `StartGame` - Command to start a new game
- `StopGame` - Command to stop/reset
- `PauseGame` - Command to pause
- `ResumeGame` - Command to resume
- `ControllerHandshake` - Initial connection handshake
- `GameSetup` - Game configuration (11 parameters + 9 lock flags)

**Event Classes** (received from server):

- `GameStartedEventForObserver`
- `GameEndedEventForObserver`
- `RoundStartedEvent`
- `RoundEndedEventForObserver`
- `TickEventForObserver`
- Plus 8 more event types

**Result Classes**:

- `ResultsForObserver` - Per-bot scoring and stats

---

## 2. METHODS TO START A BATTLE PROGRAMMATICALLY

### Method Analysis

#### ✅ What You CAN Do

1. **Create a message** with battle config:

   ```python
   from robocode_tank_royale.schema import StartGame, GameSetup, BotAddress
   
   start_game_msg = StartGame(
       bot_addresses=[...],
       game_setup=GameSetup(...),
       type=Message.Type.START_GAME
   )
   ```

2. **Send it over WebSocket** to the server
3. **Receive event messages** back from server

#### ❌ What You CAN'T Do

- No built-in method to send messages
- No async wrapper (WebSocketHandler is bot-specific)
- No sync helper function
- No configuration builder
- No connection manager (except for bot connections)

#### Recommended Implementation

Create your own wrapper (see `example_battle_orchestrator.py` for reference):

```python
class BattleController:
    async def connect(self, server_url):
        self.websocket = await websockets.connect(server_url)
        # Send handshake
        
    async def start_battle(self, bots, game_config):
        # Send StartGame message
        await self.websocket.send(json.dumps(asdict(start_game_msg)))
        
    async def receive_events(self):
        # Listen for GameStarted, Tick, RoundEnded, GameEnded events
```

---

## 3. BATTLE CONFIGURATION METHODS

### GameSetup Class - Full Configuration

**Available to configure:**

- ✅ Arena dimensions (width, height)
- ✅ Number of rounds
- ✅ Minimum/maximum participants
- ✅ Game type (melee, 1v1, custom)
- ✅ Gun cooling rate
- ✅ Inactivity timeout
- ✅ Turn timeout (milliseconds)
- ✅ Ready timeout (milliseconds)
- ✅ Ticks per second (TPS)
- ✅ Lock flags (control what server allows)

**Constructor Signature:**

```python
GameSetup(
    game_type: str,
    arena_width: int,
    is_arena_width_locked: bool,
    arena_height: int,
    is_arena_height_locked: bool,
    min_number_of_participants: int,
    is_min_number_of_participants_locked: bool,
    is_max_number_of_participants_locked: bool,
    number_of_rounds: int,
    is_number_of_rounds_locked: bool,
    gun_cooling_rate: float,
    is_gun_cooling_rate_locked: bool,
    max_inactivity_turns: int,
    is_max_inactivity_turns_locked: bool,
    turn_timeout: int,
    is_turn_timeout_locked: bool,
    ready_timeout: int,
    is_ready_timeout_locked: bool,
    default_turns_per_second: int,
    max_number_of_participants: int = None
)
```

**Gotcha**: ALL parameters are required, including the nine `is_*_locked` flags.

### BotAddress Class - Specify Participants

```python
BotAddress(
    host: str,  # Hostname or IP
    port: int   # Bot's listening port
)
```

---

## 4. GETTING BATTLE RESULTS & SCORES

### ResultsForObserver - What's Available

Sent in:

- `RoundEndedEventForObserver.results` (per-round)
- `GameEndedEventForObserver.results` (final)

**Fields available:**

```python
ResultsForObserver(
    id: int,                  # Bot ID
    name: str,                # Bot name
    version: str,             # Bot version
    rank: int,                # Final placement (1st, 2nd, etc)
    survival: int,            # Points for staying alive
    last_survivor_bonus: int, # Bonus for being last
    bullet_damage: int,       # Total damage dealt by bullets
    bullet_kill_bonus: int,   # Bonus points for bullet kills
    ram_damage: int,          # Total damage from ramming
    ram_kill_bonus: int,      # Bonus points for ram kills
    total_score: int,         # Overall score
    first_places: int,        # Times placed 1st (multi-round)
    second_places: int,       # Times placed 2nd
    third_places: int,        # Times placed 3rd
)
```

### How to Access

```python
# In GameEndedEventForObserver event
for result in event['results']:
    bot_name = result['name']
    final_score = result['total_score']
    rank = result['rank']
```

---

## 5. MONITORING BATTLE STATUS

### Available Events

| Event | When Sent | Info Provided |
|-------|-----------|---------------|
| `GameStartedEventForObserver` | Game starts | Participants, initial positions |
| `RoundStartedEvent` | Each round starts | Round number |
| `TickEventForObserver` | Each game tick | Bot positions, energy, bullet states |
| `RoundEndedEventForObserver` | Round ends | Round results, scoring |
| `GameEndedEventForObserver` | Game complete | Final results for all bots |
| `GamePausedEventForObserver` | Game paused | - |
| `GameResumedEventForObserver` | Game resumed | - |
| `GameAbortedEvent` | Game aborted | - |
| `TpsChangedEvent` | TPS adjusted | New TPS value |

### Monitoring Strategy

```python
async def monitor_battle(websocket):
    while True:
        msg = await websocket.recv()
        msg_type = msg['type']
        
        if msg_type == 'TickEventForObserver':
            # Current game state - sent frequently!
            turn = msg['turn_number']
            bots = msg['bots']  # Current positions/energy
            bullets = msg['bullets']
            
        elif msg_type == 'RoundEndedEventForObserver':
            # Check inter-round results
            results = msg['results']
            
        elif msg_type == 'GameEndedEventForObserver':
            # Final results - game is over
            final_results = msg['results']
            break
```

---

## 6. WEBSOCKET PROTOCOL & API

### Connection Protocol

**Flow:**

```
1. CONNECT to ws://server:7654
2. SEND ControllerHandshake
3. RECEIVE ServerHandshake
4. SEND StartGame
5. ... RECEIVE game events ...
6. RECEIVE GameEndedEventForObserver
7. SEND StopGame
```

### Message Format (JSON)

All messages have `type` field:

```json
{
  "type": "StartGame",
  "bot_addresses": [...],
  "game_setup": {...}
}
```

### ControllerHandshake Format

```python
ControllerHandshake(
    session_id="unique-id",        # Arbitrary string
    name="MyController",           # Your controller name
    version="1.0.0",               # Your version
    type=Message.Type.CONTROLLER_HANDSHAKE,
    author="Me",                   # Optional
    secret="server-secret"         # Optional, for auth
)
```

### Required Libraries

```python
import websockets            # WebSocket client
import json                  # JSON serialization
from dataclasses import asdict  # Convert objects to dicts
```

### Message Serialization

```python
from dataclasses import asdict
import json

# Send: Object → JSON
msg_dict = asdict(start_game_message)
json_str = json.dumps(msg_dict)
await websocket.send(json_str)

# Receive: JSON → dict
received_json = await websocket.recv()
msg_dict = json.loads(received_json)
```

### Authentication

- **With server secret**: Include `secret` parameter in ControllerHandshake
- **Example**: `secret="j1etPtYUMVuCWGUlW6hF6AV"`
- Server responds with confirmation in ServerHandshake

---

## 7. EVENT/CALLBACK SYSTEM

### Available

✅ **Event types** from server (10+ different ones)

### NOT Available

❌ **No built-in listener/callback system**  
❌ **No event registration**  
❌ **No async context managers**  

### What You Need to Do

Implement your own event handling:

```python
async def handle_events(websocket):
    while True:
        msg = await websocket.recv()
        event_type = msg['type']
        
        if event_type == 'GameStartedEventForObserver':
            on_game_started(msg)
        elif event_type == 'RoundEndedEventForObserver':
            on_round_ended(msg)
        elif event_type == 'GameEndedEventForObserver':
            on_game_ended(msg)
            break
```

Or use an event queue:

```python
from asyncio import Queue

event_queue = Queue()

async def receive_events():
    while True:
        msg = await websocket.recv()
        await event_queue.put(msg)

async def process_events():
    while True:
        event = await event_queue.get()
        # Process event
```

---

## 8. KEY LIMITATIONS & GOTCHAS

| Limitation | Impact | Workaround |
|-----------|--------|-----------|
| **No Controller class** | Must build from scratch | Create wrapper around WebSocket |
| **GameSetup all-required fields** | Tedious initialization | Create builder/helper function |
| **Async-only WebSocket** | Can't use in sync code | Use `asyncio.run()` or threading |
| **No JSON serialization methods** | Manual conversion needed | Use `dataclasses.asdict()` |
| **Lock flags on server** | Can't override certain settings | Check `ServerHandshake.game_setup` |
| **TickEventForObserver frequency** | High message volume | Sample or filter ticks |
| **No direct bot callbacks** | Observer-only perspective | Monitor via events |
| **All fields must match server** | Validation errors if mismatched | Use server's GameSetup as base |

---

## 9. BEST APPROACH FOR ORCHESTRATING BATTLES

### Recommended: Build a Thin Async Wrapper

```python
class BattleController:
    # Handles:
    # - WebSocket connection
    # - Message serialization
    # - Event loop management
    # - Results collection
    
    async def start_and_wait(self, bots, game_config):
        # Connect → Handshake → StartGame → Wait for end
        # Return results when GameEndedEventForObserver received
```

**Pros:**

- Clean API
- Proper async/await
- Easy to test

**Cons:**

- Must implement yourself
- Need asyncio knowledge

### Alternative: Use websockets Directly

```python
ws = await websockets.connect("ws://server:7654")
await ws.send(json.dumps(asdict(handshake_msg)))
# ... manage protocol manually
```

**Pros:**

- Maximum control

**Cons:**

- More error-prone
- Verbose code

### For Sync Code

```python
def start_battle_sync(bots, config):
    # Run async code synchronously
    return asyncio.run(_start_battle_async(bots, config))
```

---

## 10. PACKAGE STRUCTURE SUMMARY

```
robocode_tank_royale/
├── bot_api/
│   ├── Bot                    # Base class for implementing bots
│   ├── BotInfo                # Load bot from JSON
│   ├── GameSetup              # Game config
│   ├── events/                # 20+ event classes
│   ├── internal/
│   │   ├── websocket_handler/ # Async WebSocket (bot-specific)
│   │   └── ...
│   └── mapper/                # Object mappers
│
└── schema/
    ├── Message                # Message.Type enum (39 types)
    ├── StartGame              # Command ✓
    ├── StopGame               # Command ✓
    ├── GameSetup              # Config ✓
    ├── GameStartedEventForObserver    # Event ✓
    ├── GameEndedEventForObserver      # Event ✓
    ├── RoundStartedEvent              # Event ✓
    ├── RoundEndedEventForObserver     # Event ✓
    ├── TickEventForObserver           # Event ✓
    ├── ResultsForObserver             # Results ✓
    └── ... (24 more message types)
```

---

## 11. FILES PROVIDED IN RESEARCH

1. **RESEARCH_SUMMARY.md** - Complete reference guide
2. **WEBSOCKET_PROTOCOL_REFERENCE.md** - JSON message examples
3. **example_battle_orchestrator.py** - Working example implementation
4. **protocol_analysis.py** - Analysis script used in research

---

## FINDINGS CHECKLIST

| Item | Status | Details |
|------|--------|---------|
| Classes for controlling battles | ❌ None | Must implement with WebSocket |
| StartGame command | ✅ Available | `robocode_tank_royale.schema.StartGame` |
| Game configuration | ✅ Full control | GameSetup with 20 total params |
| Configure rounds | ✅ Yes | `number_of_rounds` parameter |
| Configure timeouts | ✅ Yes | `turn_timeout`, `ready_timeout` |
| Configure inactivity | ✅ Yes | `max_inactivity_turns` |
| Get battle results | ✅ Yes | `GameEndedEventForObserver` |
| Get round results | ✅ Yes | `RoundEndedEventForObserver` |
| Monitor battle | ✅ Partial | TickEventForObserver (high volume) |
| Events for lifecycle | ✅ Yes | 10+ event types |
| WebSocket protocol | ✅ Documented | Message classes for all types |
| Async support | ✅ Yes | Based on `websockets` lib |
| Sync support | ❌ No | Must wrap async yourself |
| Authentication | ✅ Yes | Secret in ControllerHandshake |

---

## CONCLUSION

The `robocode-tank-royale` package provides **message classes and schemas** for communicating with the Tank Royale server, but **no battle orchestration framework**.

You must:

1. Connect to the server via WebSocket (using `websockets` library)
2. Implement the controller protocol (handshake → start → listen → stop)
3. Handle serialization of message objects to/from JSON
4. Manage the event loop for async message handling

The package is **sufficient in scope** (all necessary message types exist) but **requires implementation** at the application level.

**Recommended starting point**: Copy and modify the `example_battle_orchestrator.py` provided in research files.
