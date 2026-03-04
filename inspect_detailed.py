import inspect
from robocode_tank_royale.schema import (
    StartGame,
    GameSetup,
    StopGame,
    GameStartedEventForBot,
    GameEndedEventForBot,
    GameStartedEventForObserver,
    GameEndedEventForObserver,
    ControllerHandshake,
    ObserverHandshake,
    PauseGame,
    ResumeGame,
    Message,
    Participant,
    ResultsForBot,
    ResultsForObserver,
    RoundStartedEvent,
    RoundEndedEventForBot,
    RoundEndedEventForObserver,
)

print("=" * 80)
print("KEY MESSAGE CLASSES FOR BATTLE CONTROL")
print("=" * 80)

classes_to_inspect = {
    "StartGame": StartGame,
    "GameSetup": GameSetup,
    "StopGame": StopGame,
    "PauseGame": PauseGame,
    "ResumeGame": ResumeGame,
    "ControllerHandshake": ControllerHandshake,
    "ObserverHandshake": ObserverHandshake,
    "GameStartedEventForBot": GameStartedEventForBot,
    "GameStartedEventForObserver": GameStartedEventForObserver,
    "GameEndedEventForBot": GameEndedEventForBot,
    "GameEndedEventForObserver": GameEndedEventForObserver,
    "ResultsForBot": ResultsForBot,
    "ResultsForObserver": ResultsForObserver,
    "RoundStartedEvent": RoundStartedEvent,
    "RoundEndedEventForBot": RoundEndedEventForBot,
    "RoundEndedEventForObserver": RoundEndedEventForObserver,
}

for class_name, cls in classes_to_inspect.items():
    print(f"\n{'='*80}")
    print(f"Class: {class_name}")
    print(f"{'='*80}")

    try:
        # Get fields (for dataclasses)
        if hasattr(cls, "__dataclass_fields__"):
            print("Fields:")
            for field_name, field in cls.__dataclass_fields__.items():
                field_type = field.type
                print(f"  {field_name}: {field_type}")
    except Exception as e:
        print(f"No dataclass fields: {e}")

    # Get constructor signature
    try:
        sig = inspect.signature(cls.__init__)
        print(f"\nConstructor signature:")
        print(f"  {cls.__name__}{sig}")
    except Exception as e:
        print(f"Could not get signature: {e}")

    # Get docstring
    doc = cls.__doc__
    if doc:
        print(f"\nDocstring:")
        print(f"  {doc}")

    # Get methods
    methods = [
        m for m in dir(cls) if not m.startswith("_") and callable(getattr(cls, m))
    ]
    if methods:
        print(f"\nMethods: {', '.join(methods[:10])}")
        if len(methods) > 10:
            print(f"  ... and {len(methods)-10} more")

print("\n" + "=" * 80)
print("GAMSETUP DETAILS")
print("=" * 80)

# Deep dive into GameSetup since it seems central to configuration
gs = GameSetup(
    battle_width=800,
    battle_height=600,
    number_of_rounds=3,
    gun_cooling_rate=0.1,
    inactivity_timeout=300,
    turn_timeout=30000,
    max_inactivity_turns=50,
    tps=30,
)
print(f"GameSetup instance: {gs}")

print("\n" + "=" * 80)
print("MESSAGE CLASS HIERARCHY")
print("=" * 80)

print(f"Message base class: {Message}")
print(f"Message members: {[m for m in dir(Message) if not m.startswith('_')]}")

print("\n" + "=" * 80)
print("Check for internal/WebSocket modules")
print("=" * 80)

try:
    from robocode_tank_royale.bot_api.internal import websocket_handler

    print("Found websocket_handler module")
    print(dir(websocket_handler))
except Exception as e:
    print(f"Could not import websocket_handler: {e}")

# Try to find controller-related classes
try:
    import robocode_tank_royale

    print("\nSearching for 'Controller' related items...")
    for item in dir(robocode_tank_royale):
        if "controller" in item.lower():
            print(f"  Found: {item}")
except Exception as e:
    print(f"Error: {e}")

print("\nDone!")
