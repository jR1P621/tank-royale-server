"""
WebSocket Protocol Reference for Tank Royale

This document shows the exact JSON format of messages sent/received
from the Tank Royale server.
"""

# ============================================================================

# OUTGOING MESSAGES (Controller sends to Server)

# ============================================================================

# 1. CONTROLLER HANDSHAKE (sent immediately after WebSocket connection)

CONTROLLER_HANDSHAKE = {
    "type": "ControllerHandshake",
    "session_id": "my-session-123",
    "name": "MyBattleController",
    "version": "1.0.0",
    "author": "Me",
    "secret": "j1etPtYUMVuCWGUlW6hF6AV"  # Optional, only if server requires auth
}

# 2. START GAME (initiate a new battle)

START_GAME = {
    "type": "StartGame",
    "bot_addresses": [
        {"host": "neural-bot-001", "port": 9001},
        {"host": "neural-bot-002", "port": 9001},
        {"host": "neural-bot-003", "port": 9001},
    ],
    "game_setup": {
        "game_type": "melee",
        "arena_width": 800,
        "arena_height": 600,
        "min_number_of_participants": 3,
        "max_number_of_participants": 10,
        "number_of_rounds": 3,
        "gun_cooling_rate": 0.1,
        "max_inactivity_turns": 50,
        "turn_timeout": 30000,           # milliseconds
        "ready_timeout": 10000,          # milliseconds
        "default_turns_per_second": 30,
        # All lock flags must be present (True = server locked this setting)
        "is_arena_width_locked": False,
        "is_arena_height_locked": False,
        "is_min_number_of_participants_locked": False,
        "is_max_number_of_participants_locked": False,
        "is_number_of_rounds_locked": False,
        "is_gun_cooling_rate_locked": False,
        "is_max_inactivity_turns_locked": False,
        "is_turn_timeout_locked": False,
        "is_ready_timeout_locked": False,
    }
}

# 3. PAUSE GAME (pause execution, game continues counting)

PAUSE_GAME = {
    "type": "PauseGame"
}

# 4. RESUME GAME (resume from pause)

RESUME_GAME = {
    "type": "ResumeGame"
}

# 5. CHANGE TPS (adjust speed during execution)

CHANGE_TPS = {
    "type": "ChangeTps",
    "tps": 60  # New ticks per second
}

# 6. STOP GAME (stop and reset)

STOP_GAME = {
    "type": "StopGame"
}

# ============================================================================

# INCOMING MESSAGES (Server sends to Controller)

# ============================================================================

# 1. SERVER HANDSHAKE (response to ControllerHandshake)

SERVER_HANDSHAKE = {
    "type": "ServerHandshake",
    "game_setup": {
        # Same structure as in START_GAME
        "game_type": "melee",
        "arena_width": 800,
        "arena_height": 600,
        "min_number_of_participants": 1,
        "max_number_of_participants": 10,
        "number_of_rounds": 10,
        "gun_cooling_rate": 0.04,
        "max_inactivity_turns": 150,
        "turn_timeout": 30000,
        "ready_timeout": 10000,
        "default_turns_per_second": 30,
        # Lock flags show server restrictions
        "is_arena_width_locked": True,    # Cannot change
        "is_arena_height_locked": True,   # Cannot change
        "is_min_number_of_participants_locked": False,
        "is_max_number_of_participants_locked": False,
        "is_number_of_rounds_locked": False,
        "is_gun_cooling_rate_locked": True,  # Cannot change
        "is_max_inactivity_turns_locked": True,  # Cannot change
        "is_turn_timeout_locked": True,   # Cannot change
        "is_ready_timeout_locked": True,  # Cannot change
    },
    "server_secret": "some-random-secret"
}

# 2. GAME STARTED EVENT (game initialization complete)

GAME_STARTED_EVENT_FOR_OBSERVER = {
    "type": "GameStartedEventForObserver",
    "game_setup": {
        # Server's final game setup (includes overrides if any)
        "game_type": "melee",
        "arena_width": 800,
        "arena_height": 600,
        "min_number_of_participants": 2,
        "max_number_of_participants": 10,
        "number_of_rounds": 3,
        "gun_cooling_rate": 0.1,
        "max_inactivity_turns": 50,
        "turn_timeout": 30000,
        "ready_timeout": 10000,
        "default_turns_per_second": 30,
        "is_arena_width_locked": False,
        "is_arena_height_locked": False,
        "is_min_number_of_participants_locked": False,
        "is_max_number_of_participants_locked": False,
        "is_number_of_rounds_locked": False,
        "is_gun_cooling_rate_locked": False,
        "is_max_inactivity_turns_locked": False,
        "is_turn_timeout_locked": False,
        "is_ready_timeout_locked": False,
    },
    "participants": [
        {
            "id": 1,
            "name": "NeuralBot-001",
            "version": "1.0",
            "initial_position": {
                "x": 100,
                "y": 100,
                "direction": 0
            }
        },
        {
            "id": 2,
            "name": "NeuralBot-002",
            "version": "1.0",
            "initial_position": {
                "x": 700,
                "y": 500,
                "direction": 180
            }
        },
        # ... more participants
    ]
}

# 3. ROUND STARTED EVENT

ROUND_STARTED_EVENT = {
    "type": "RoundStartedEvent",
    "round_number": 1
}

# 4. TICK EVENT (game state each turn - sent frequently!)

TICK_EVENT_FOR_OBSERVER = {
    "type": "TickEventForObserver",
    "turn_number": 42,
    "bots": [
        {
            "id": 1,
            "x": 150.5,
            "y": 200.3,
            "direction": 45.2,
            "speed": 5.0,
            "energy": 85.5,
            "gun_direction": 90.0,
            "radar_direction": 90.0,
            "color": {"red": 255, "green": 0, "blue": 0}
        },
        {
            "id": 2,
            "x": 650.1,
            "y": 450.7,
            "direction": 225.8,
            "speed": 3.0,
            "energy": 92.0,
            "gun_direction": 180.0,
            "radar_direction": 180.0,
            "color": {"red": 0, "green": 255, "blue": 0}
        },
    ],
    "bullets": [
        {
            "id": 1,
            "x": 200.0,
            "y": 250.0,
            "direction": 45.0,
            "power": 1.0,
            "owner_id": 1,
            "color": {"red": 255, "green": 255, "blue": 0}
        },
        # ... more bullets
    ]
}

# 5. ROUND ENDED EVENT

ROUND_ENDED_EVENT_FOR_OBSERVER = {
    "type": "RoundEndedEventForObserver",
    "round_number": 1,
    "turn_number": 450,
    "results": [
        {
            "id": 1,
            "name": "NeuralBot-001",
            "version": "1.0",
            "rank": 1,
            "survival": 100,
            "last_survivor_bonus": 50,
            "bullet_damage": 200,
            "bullet_kill_bonus": 150,
            "ram_damage": 0,
            "ram_kill_bonus": 0,
            "total_score": 500,
            "first_places": 1,
            "second_places": 0,
            "third_places": 0
        },
        {
            "id": 2,
            "name": "NeuralBot-002",
            "version": "1.0",
            "rank": 2,
            "survival": 0,
            "last_survivor_bonus": 0,
            "bullet_damage": 150,
            "bullet_kill_bonus": 0,
            "ram_damage": 0,
            "ram_kill_bonus": 0,
            "total_score": 150,
            "first_places": 0,
            "second_places": 1,
            "third_places": 0
        },
    ]
}

# 6. GAME ENDED EVENT (all rounds complete)

GAME_ENDED_EVENT_FOR_OBSERVER = {
    "type": "GameEndedEventForObserver",
    "number_of_rounds": 3,
    "results": [
        {
            "id": 1,
            "name": "NeuralBot-001",
            "version": "1.0",
            "rank": 1,
            "survival": 280,
            "last_survivor_bonus": 100,
            "bullet_damage": 650,
            "bullet_kill_bonus": 450,
            "ram_damage": 0,
            "ram_kill_bonus": 0,
            "total_score": 1480,
            "first_places": 3,
            "second_places": 0,
            "third_places": 0
        },
        {
            "id": 2,
            "name": "NeuralBot-002",
            "version": "1.0",
            "rank": 2,
            "survival": 150,
            "last_survivor_bonus": 0,
            "bullet_damage": 550,
            "bullet_kill_bonus": 100,
            "ram_damage": 0,
            "ram_kill_bonus": 0,
            "total_score": 800,
            "first_places": 0,
            "second_places": 3,
            "third_places": 0
        },
    ]
}

# 7. GAME PAUSED EVENT

GAME_PAUSED_EVENT_FOR_OBSERVER = {
    "type": "GamePausedEventForObserver"
}

# 8. GAME RESUMED EVENT

GAME_RESUMED_EVENT_FOR_OBSERVER = {
    "type": "GameResumedEventForObserver"
}

# 9. GAME ABORTED EVENT (something went wrong)

GAME_ABORTED_EVENT = {
    "type": "GameAbortedEvent"
}

# 10. TPS CHANGED EVENT

TPS_CHANGED_EVENT = {
    "type": "TpsChangedEvent",
    "tps": 60
}

# 11. BOT LIST UPDATE (bots available on server)

BOT_LIST_UPDATE = {
    "type": "BotListUpdate",
    "bots": [
        {
            "host": "neural-bot-001",
            "port": 9001,
            "name": "NeuralBot-001",
            "version": "1.0"
        },
        {
            "host": "neural-bot-002",
            "port": 9001,
            "name": "NeuralBot-002",
            "version": "1.0"
        },
    ]
}

# ============================================================================

# PROTOCOL FLOW DIAGRAM

# ============================================================================

"""
Controller                          Server

CONNECT (WebSocket)
      =========================================>

SEND ControllerHandshake
      =========================================>

RECEIVE ServerHandshake
      <=========================================

SEND StartGame
      =========================================>

RECEIVE GameStartedEventForObserver
      <=========================================

RECEIVE RoundStartedEvent
      <=========================================

RECEIVE TickEventForObserver (tick 1)
      <=========================================

RECEIVE TickEventForObserver (tick 2)
      <=========================================

... (many ticks per round) ...

RECEIVE RoundEndedEventForObserver
      <=========================================

RECEIVE RoundStartedEvent (next round)
      <=========================================

... (repeat for all rounds) ...

RECEIVE GameEndedEventForObserver
      <=========================================

SEND StopGame
      =========================================>

DISCONNECT
      =========================================>
"""

# ============================================================================

# KEY NOTES

# ============================================================================

"""

1. JSON Format
   - All messages are JSON objects
   - "type" field identifies message type
   - All values use lowercase field names (snake_case)

2. BotAddress Format
   - Each address is {"host": str, "port": int}
   - host: hostname or IP (must resolve from Tank Royale server)
   - port: bot's listening port

3. Color Format
   - {"red": int, "green": int, "blue": int}
   - Values 0-255

4. Coordinates
   - x, y: float values in pixels
   - direction: float 0-359.9 degrees (0 = up, 90 = right, 180 = down, 270 = left)
   - All positions are absolute within arena

5. GameSetup Lock Flags
   - True = server locked this field, cannot be overridden
   - False = can be changed when sending StartGame
   - Server responds with actual values that will be used

6. TickEventForObserver
   - Contains a snapshot of all bots and bullets each turn
   - Sent frequently (default 30 TPS = 30 per second)
   - For 3 rounds with 450 turns each: ~40,500 tick events!
   - Consider sampling or filtering in production

7. Error Handling
   - No explicit error messages in schema
   - Errors typically result in GameAbortedEvent
   - Implement timeout handling for hung games

8. Authentication
   - Use "secret" field in ControllerHandshake
   - Server responds with "server_secret" in ServerHandshake
   - Secret must match server configuration
"""
