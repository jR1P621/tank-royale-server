import inspect
from robocode_tank_royale.schema import GameSetup

print("=" * 80)
print("GAMESETUP FIELD INSPECTION")
print("=" * 80)

if hasattr(GameSetup, "__dataclass_fields__"):
    print("GameSetup fields:")
    for field_name, field in GameSetup.__dataclass_fields__.items():
        field_type = field.type
        default = field.default
        print(f"  {field_name}: {field_type} = {default}")

# Try to create an instance with proper parameters
print("\n" + "=" * 80)
print("TRYING TO CREATE GAMESETUP INSTANCE")
print("=" * 80)

try:
    gs = GameSetup(
        game_type="melee",
        arena_width=800,
        arena_height=600,
        min_number_of_participants=2,
        number_of_rounds=3,
        gun_cooling_rate=0.1,
        max_inactivity_turns=50,
        turn_timeout=30000,
        ready_timeout=10000,
        default_turns_per_second=30,
    )
    print(f"Created GameSetup successfully!")
    print(f"Instance: {gs}")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()

# Check for json serialization
print("\n" + "=" * 80)
print("CHECKING FOR MESSAGE SERIALIZATION")
print("=" * 80)

try:
    from robocode_tank_royale.schema import StartGame, BotAddress
    import json

    # Try to see if these are JSON serializable
    start_msg = StartGame(bot_addresses=None, type=None, game_setup=None)
    print(f"StartGame instance created: {start_msg}")

    # Check if it has a to_dict or similar method
    print(
        f"\nMethods on StartGame: {[m for m in dir(start_msg) if not m.startswith('_')]}"
    )

    # Check for dataclass conversion utilities
    from dataclasses import asdict

    try:
        msg_dict = asdict(start_msg)
        print(f"Converted to dict: {msg_dict}")
    except Exception as e:
        print(f"Could not convert to dict: {e}")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()

# Look for WebSocket communication
print("\n" + "=" * 80)
print("WEBSOCKET AND INTERNAL MODULES")
print("=" * 80)

try:
    from robocode_tank_royale.bot_api import internal

    print(f"internal module found")
    internal_mods = [m for m in dir(internal) if not m.startswith("_")]
    print(f"Internal submodules: {internal_mods}")

    # Try to find websocket handler
    try:
        from robocode_tank_royale.bot_api.internal.websocket_handler import (
            WebSocketHandler,
        )

        print(f"\nFound WebSocketHandler")
        print(
            f"Methods: {[m for m in dir(WebSocketHandler) if not m.startswith('_')][:15]}"
        )
    except ImportError as e:
        print(f"Could not import WebSocketHandler: {e}")

except Exception as e:
    print(f"Could not import internal: {e}")

print("\nDone!")
