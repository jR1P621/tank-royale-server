"""
Example: Simple Battle Orchestrator using robocode-tank-royale

This example shows how to:
1. Connect to Tank Royale server as a Controller
2. Start a battle with multiple bots
3. Monitor events
4. Collect results
5. Stop the battle

Note: This is pseudo-code showing the key pattern.
For production use, you'd want proper error handling, timeouts, and async management.
"""

import asyncio
import json
import websockets
from dataclasses import asdict
from datetime import datetime
from typing import List, Dict, Any

from robocode_tank_royale.schema import (
    Message,
    ControllerHandshake,
    StartGame,
    GameSetup,
    BotAddress,
    StopGame,
    GameStartedEventForObserver,
    GameEndedEventForObserver,
    RoundStartedEvent,
    RoundEndedEventForObserver,
    TickEventForObserver,
)


class SimpleBattleOrchestrator:
    """
    A simple synchronous wrapper around Tank Royale WebSocket protocol.
    """

    def __init__(self, server_url: str, server_secret: str = None):
        """
        Args:
            server_url: WebSocket URL, e.g., "ws://localhost:7654"
            server_secret: Secret for authentication (optional)
        """
        self.server_url = server_url
        self.server_secret = server_secret
        self.websocket = None
        self.game_results = None
        self.is_connected = False

    async def connect(self) -> None:
        """Connect to Tank Royale server."""
        print(f"Connecting to {self.server_url}...")
        self.websocket = await websockets.connect(self.server_url)

        # Send ControllerHandshake
        handshake = ControllerHandshake(
            session_id="orchestrator-001",
            name="SimpleBattleController",
            version="1.0.0",
            author="Example",
            secret=self.server_secret,
            type=Message.Type.CONTROLLER_HANDSHAKE,
        )

        await self._send_message(handshake)

        # Wait for ServerHandshake
        msg = await self._receive_message()
        print(f"Received handshake: {msg['type']}")
        self.is_connected = True

    async def start_battle(
        self,
        bots: List[Dict[str, Any]],
        num_rounds: int = 3,
        arena_width: int = 800,
        arena_height: int = 600,
        tps: int = 30,
    ) -> Dict[str, Any]:
        """
        Start a battle with given bots.

        Args:
            bots: List of dicts with 'host' and 'port' keys
            num_rounds: Number of rounds to play
            arena_width: Arena width in pixels
            arena_height: Arena height in pixels
            tps: Ticks per second

        Returns:
            Dictionary with battle results
        """

        if not self.is_connected:
            await self.connect()

        # Create GameSetup
        game_setup = GameSetup(
            game_type="melee",
            arena_width=arena_width,
            arena_height=arena_height,
            min_number_of_participants=len(bots),
            max_number_of_participants=len(bots),
            number_of_rounds=num_rounds,
            gun_cooling_rate=0.1,
            max_inactivity_turns=50,
            turn_timeout=30000,
            ready_timeout=10000,
            default_turns_per_second=tps,
            # All lock flags - set to False to allow changes
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

        # Create BotAddress list
        bot_addresses = [BotAddress(host=bot["host"], port=bot["port"]) for bot in bots]

        # Send StartGame
        start_msg = StartGame(
            bot_addresses=bot_addresses,
            game_setup=game_setup,
            type=Message.Type.START_GAME,
        )

        print(f"Starting battle with {len(bots)} bots for {num_rounds} rounds...")
        await self._send_message(start_msg)

        # Collect events until game ends
        results = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "events": [],
            "final_results": None,
        }

        try:
            while True:
                msg = await self._receive_message()
                msg_type = msg.get("type")

                if msg_type == "GameStartedEventForObserver":
                    print(
                        f"✓ Game started with {len(msg.get('participants', []))} participants"
                    )
                    results["events"].append(("game_started", msg))

                elif msg_type == "RoundStartedEvent":
                    round_num = msg.get("round_number", 0)
                    print(f"  Round {round_num} started")
                    results["events"].append(("round_started", msg))

                elif msg_type == "TickEventForObserver":
                    # Optional: log tick events (can be verbose)
                    pass

                elif msg_type == "RoundEndedEventForObserver":
                    round_num = msg.get("round_number", 0)
                    print(f"  Round {round_num} ended")
                    results["events"].append(("round_ended", msg))

                elif msg_type == "GameEndedEventForObserver":
                    print("✓ Game ended!")
                    results["status"] = "completed"
                    results["final_results"] = msg
                    results["completed_at"] = datetime.now().isoformat()
                    break

                elif msg_type == "GameAbortedEvent":
                    print("✗ Game aborted!")
                    results["status"] = "aborted"
                    break

                else:
                    print(f"  Received: {msg_type}")
                    results["events"].append((msg_type, msg))

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
            results["status"] = "disconnected"

        # Send StopGame to reset
        await self._send_message(StopGame(type=Message.Type.STOP_GAME))

        return results

    async def disconnect(self) -> None:
        """Disconnect from server."""
        if self.websocket:
            await self.websocket.close()
        self.is_connected = False

    async def _send_message(self, message: Any) -> None:
        """Send a message to the server."""
        msg_dict = asdict(message)
        json_str = json.dumps(msg_dict)
        await self.websocket.send(json_str)
        print(f">>> Sent {message.type}")

    async def _receive_message(self) -> Dict[str, Any]:
        """Receive a message from the server."""
        msg = await self.websocket.recv()
        if isinstance(msg, bytes):
            msg = msg.decode("utf-8")
        return json.loads(msg)


async def main():
    """Example usage."""

    # Server configuration
    SERVER_URL = "ws://tank-royale-server:7654"
    SERVER_SECRET = "j1etPtYUMVuCWGUlW6hF6AV"

    # Bot configuration
    BOTS = [
        {"host": "neural-bot-001", "port": 9001},
        {"host": "neural-bot-002", "port": 9001},
        {"host": "neural-bot-003", "port": 9001},
    ]

    # Create orchestrator
    orchestrator = SimpleBattleOrchestrator(SERVER_URL, SERVER_SECRET)

    try:
        # Start battle
        results = await orchestrator.start_battle(bots=BOTS, num_rounds=3, tps=30)

        # Print results
        print("\n" + "=" * 80)
        print("BATTLE RESULTS")
        print("=" * 80)
        print(f"Status: {results['status']}")
        print(f"Started: {results['started_at']}")

        if results["final_results"]:
            final = results["final_results"]
            print(f"\nFinal Scores:")
            for res in final.get("results", []):
                print(
                    f"  {res.get('name'):20} - "
                    f"Rank: {res.get('rank')}, "
                    f"Score: {res.get('total_score')}"
                )

    finally:
        await orchestrator.disconnect()


# ============================================================================
# SYNCHRONOUS WRAPPER (for non-async code)
# ============================================================================


def start_battle_sync(
    server_url: str, bots: List[Dict[str, str]], num_rounds: int = 3, **kwargs
) -> Dict[str, Any]:
    """
    Synchronous wrapper for starting a battle.

    Usage:
        results = start_battle_sync(
            "ws://localhost:7654",
            [{"host": "bot-1", "port": 9001}],
            num_rounds=3
        )
    """
    orchestrator = SimpleBattleOrchestrator(server_url)
    results = asyncio.run(
        orchestrator.start_battle(bots, num_rounds=num_rounds, **kwargs)
    )
    return results


if __name__ == "__main__":
    # Run example
    asyncio.run(main())
