"""
Battle Orchestrator for Tank Royale Neural Bot Simulation

Connects to Tank Royale server as a controller and automatically manages battles:
1. Waits for neural bots to connect to the server
2. Once enough bots are connected, starts a battle
3. Monitors battle progress and collects results
4. Logs results in a format that simulate.py can parse
"""

import asyncio
import json
import logging
import os
import random
import time
import websockets
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Any, Optional

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)


class BattleOrchestrator:
    """Manages automatic battle orchestration for neural bot simulation."""

    def __init__(
        self,
        server_url: str,
        controller_secret: str,
        min_bots: int = 2,
        max_bots: int = 20,
        num_rounds: int = 1,
        turns_per_round: int = 300,
        arena_width: int = 1200,
        arena_height: int = 900,
        tps: int = 30,
        timeout: int = 300,
        tick_log_interval: int = 100,
        expected_neural_bots: int = 0,
        required_non_neural_bots: int = 0,
        neural_host_prefix: str = "neural-bot-",
        pre_start_quiet_period: float = 1.5,
        post_battle_cool_down: float = 10.0,
    ):
        """
        Initialize the battle orchestrator.

        Args:
            server_url: WebSocket URL of Tank Royale server (e.g., "ws://localhost:7654")
            controller_secret: Controller secret for authentication
            min_bots: Minimum bots needed to start a battle
            max_bots: Maximum bots to include in a battle
            num_rounds: Number of rounds per battle
            turns_per_round: Maximum turns per round (inactivity timeout)
            arena_width: Arena width in pixels
            arena_height: Arena height in pixels
            tps: Ticks per second
            timeout: Timeout in seconds for waiting for bots to connect
            tick_log_interval: Log tick progress every N turns (0 disables)
            post_battle_cool_down: Time in seconds to wait after battle ends before starting next (allows bot cleanup)
        """
        self.server_url = server_url
        self.controller_secret = controller_secret
        self.min_bots = min_bots
        self.max_bots = max_bots
        self.num_rounds = num_rounds
        self.turns_per_round = turns_per_round
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.tps = tps
        self.timeout = timeout
        self.tick_log_interval = tick_log_interval
        self.expected_neural_bots = expected_neural_bots
        self.required_non_neural_bots = required_non_neural_bots
        self.neural_host_prefix = neural_host_prefix.lower()
        self.pre_start_quiet_period = max(0.0, float(pre_start_quiet_period))
        self.post_battle_cool_down = max(0.0, float(post_battle_cool_down))

        self.websocket = None
        self.is_connected = False
        self.connected_bots: Dict[str, Dict] = {}
        self.battle_in_progress = False
        self.start_time = datetime.now()
        self.bot_address_map: Dict[int, str] = {}  # Maps rank to bot name
        self.last_bot_activity = time.monotonic()
        self.last_battle_end_time = 0.0  # Track when last battle ended
        self.start_lock = asyncio.Lock()
        self.first_battle_initiated = asyncio.Event()

    @staticmethod
    def _bot_identity_key(host: str, port: Any, name: str) -> str:
        """Build a stable bot identity key, preferring host:port when available."""
        if host and port is not None:
            return f"{host}:{port}"
        if host and name:
            return f"{host}:{name}"
        return host or name

    def _is_neural_bot(self, bot_info: Dict[str, Any]) -> bool:
        """Identify neural bots by host/name prefix."""
        host = str(bot_info.get("host", "")).lower()
        name = str(bot_info.get("name", "")).lower()
        if host.startswith(self.neural_host_prefix) or name.startswith(
            self.neural_host_prefix
        ):
            return True
        return host.startswith("neuralbot-") or name.startswith("neuralbot-")

    def _partition_connected_bots(self) -> tuple[list[str], list[str]]:
        """Split connected bot hosts into neural and non-neural pools."""
        neural_hosts = []
        non_neural_hosts = []
        for host, bot_info in self.connected_bots.items():
            if self._is_neural_bot(bot_info):
                neural_hosts.append(host)
            else:
                non_neural_hosts.append(host)
        return sorted(neural_hosts), sorted(non_neural_hosts)

    def _composition_mode_enabled(self) -> bool:
        return self.expected_neural_bots > 0 or self.required_non_neural_bots > 0

    def _is_post_battle_cool_down_active(self) -> bool:
        """Check if post-battle cool-down period is still in effect."""
        if self.last_battle_end_time <= 0:
            return False
        elapsed = time.monotonic() - self.last_battle_end_time
        return elapsed < self.post_battle_cool_down

    def _can_start_battle(self) -> bool:
        """Check whether required bots are available to start a battle."""
        if self.battle_in_progress or self._is_post_battle_cool_down_active():
            return False

        if not self._composition_mode_enabled():
            return len(self.connected_bots) >= self.min_bots

        neural_hosts, non_neural_hosts = self._partition_connected_bots()

        if len(neural_hosts) < self.expected_neural_bots:
            return False
        if len(non_neural_hosts) < self.required_non_neural_bots:
            return False

        selected_total = self.expected_neural_bots + self.required_non_neural_bots
        return len(self.connected_bots) >= selected_total

    def _check_bots_still_available(self) -> bool:
        """Check if bots are still available (ignoring battle_in_progress flag).

        Used during quiet period to check if roster changed, without being
        affected by the battle_in_progress flag that was just set.
        """
        if not self._composition_mode_enabled():
            return len(self.connected_bots) >= self.min_bots

        neural_hosts, non_neural_hosts = self._partition_connected_bots()

        if len(neural_hosts) < self.expected_neural_bots:
            return False
        if len(non_neural_hosts) < self.required_non_neural_bots:
            return False

        selected_total = self.expected_neural_bots + self.required_non_neural_bots
        return len(self.connected_bots) >= selected_total

    def _selection_requirement_text(self) -> str:
        """Human-readable readiness summary for logs."""
        if not self._composition_mode_enabled():
            return f"{len(self.connected_bots)}/{self.min_bots} required"

        neural_hosts, non_neural_hosts = self._partition_connected_bots()
        return (
            f"neural {len(neural_hosts)}/{self.expected_neural_bots}, "
            f"non-neural {len(non_neural_hosts)}/{self.required_non_neural_bots}"
        )

    async def run(self) -> None:
        """Main loop: connect, wait for bots, run battles."""
        try:
            await self.connect()
            await self.wait_for_bots_and_run_battles()
        except Exception as e:
            log.error(f"Fatal error: {e}", exc_info=True)
        finally:
            await self.disconnect()

    async def connect(self) -> None:
        """Connect to Tank Royale server as a controller."""
        max_retries = 10
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                log.info(
                    f"Connecting to {self.server_url} (attempt {attempt + 1}/{max_retries})..."
                )
                self.websocket = await asyncio.wait_for(
                    websockets.connect(self.server_url), timeout=10
                )

                # Protocol order: receive ServerHandshake first, then send ControllerHandshake
                server_msg = await asyncio.wait_for(self._receive_message(), timeout=10)
                if server_msg.get("type") != "ServerHandshake":
                    raise RuntimeError(f"Unexpected response: {server_msg.get('type')}")

                server_session_id = server_msg.get("sessionId") or server_msg.get(
                    "session_id"
                )
                if not server_session_id:
                    raise RuntimeError("ServerHandshake missing sessionId")

                # Send controller handshake using the server-provided session id
                handshake_data = {
                    "type": "ControllerHandshake",
                    "sessionId": server_session_id,
                    "session_id": server_session_id,
                    "name": "NeuralBotBattleOrchestrator",
                    "version": "1.0.0",
                    "author": "Tank Royale Neural Bot",
                    "secret": self.controller_secret,
                }

                await self._send_message(handshake_data)
                log.info("Controller handshake sent")
                log.info("✓ Connected to server successfully")
                self.is_connected = True
                return

            except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
                if self.websocket:
                    try:
                        await self.websocket.close()
                    except:
                        pass
                    self.websocket = None

                if attempt < max_retries - 1:
                    log.warning(
                        f"Connection attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s..."
                    )
                    await asyncio.sleep(retry_delay)
                else:
                    raise RuntimeError(
                        f"Failed to connect after {max_retries} attempts: {e}"
                    )
            except Exception as e:
                if self.websocket:
                    try:
                        await self.websocket.close()
                    except:
                        pass
                    self.websocket = None
                raise RuntimeError(f"Connection failed: {e}")

    async def wait_for_bots_and_run_battles(self) -> None:
        """Wait for bots to connect, then run battles."""
        log.info(
            f"Waiting for {self.min_bots}-{self.max_bots} bots to connect (timeout: {self.timeout}s)..."
        )

        message_task = asyncio.create_task(self._listen_for_bots())
        try:
            if self.timeout > 0:
                try:
                    await asyncio.wait_for(
                        self.first_battle_initiated.wait(), timeout=self.timeout
                    )
                except asyncio.TimeoutError:
                    if not self.first_battle_initiated.is_set():
                        log.warning(
                            f"Timeout after {self.timeout}s - starting with {len(self.connected_bots)} bots"
                        )
                        await self._try_start_battle(trigger="initial-timeout")

            # Keep listener alive for full orchestrator lifetime
            await message_task

        except asyncio.TimeoutError:
            # Defensive fallback: timeout is handled above via wait_for(first battle)
            if not self.first_battle_initiated.is_set():
                log.warning(
                    f"Timeout after {self.timeout}s - starting with {len(self.connected_bots)} bots"
                )
                await self._try_start_battle(trigger="timeout-fallback")

        except asyncio.CancelledError:
            message_task.cancel()
            try:
                await message_task
            except asyncio.CancelledError:
                pass
            log.info("Orchestrator cancelled")
            raise

    async def _try_start_battle(self, trigger: str) -> bool:
        """Attempt to start a battle with serialization to avoid concurrent starts."""
        async with self.start_lock:
            if not self._can_start_battle():
                if not self.battle_in_progress:
                    log.warning(
                        f"Not enough bots to start after {trigger} "
                        f"({self._selection_requirement_text()})"
                    )
                return False

            log.info(f"Starting battle with {len(self.connected_bots)} bots")
            await self.start_battle()
            return True

    async def _listen_for_bots(self) -> None:
        """Listen for bot connections in the lobby."""
        while True:
            try:
                msg = await self._receive_message()
                msg_type = msg.get("type")

                if msg_type == "BotListUpdate":
                    bots = msg.get("bots", [])
                    self.last_bot_activity = time.monotonic()
                    previous_bot_ids = set(self.connected_bots.keys())

                    updated_bots = {}
                    for bot in bots:
                        host = bot.get("host") or ""
                        name = bot.get("name") or host
                        port = bot.get("port")
                        bot_id = self._bot_identity_key(host, port, name)
                        if not bot_id:
                            continue
                        updated_bots[bot_id] = {
                            "host": host,
                            "port": port,
                            "name": name,
                            "version": bot.get("version", "1.0.0"),
                            "connected_at": self.connected_bots.get(bot_id, {}).get(
                                "connected_at", datetime.now().isoformat()
                            ),
                        }

                    self.connected_bots = updated_bots
                    new_bot_ids = set(self.connected_bots.keys()) - previous_bot_ids
                    for bot_id in sorted(new_bot_ids):
                        bot_info = self.connected_bots[bot_id]
                        bot_name = bot_info["name"]
                        bot_host = bot_info.get("host")
                        bot_port = bot_info.get("port")
                        log.info(f"✓ Bot available: {bot_name} ({bot_host}:{bot_port})")

                    log.info(
                        f"Lobby bots available: {self._selection_requirement_text()}"
                    )

                elif msg_type == "BotConnectionHandshake":
                    self.last_bot_activity = time.monotonic()
                    bot_name = msg.get("name", "Unknown")
                    bot_version = msg.get("version", "1.0.0")
                    host = msg.get("host") or bot_name
                    port = msg.get("port")
                    log.info(f"✓ Bot connected: {bot_name} ({host}:{port})")
                    bot_id = self._bot_identity_key(host, port, bot_name)
                    self.connected_bots[bot_id] = {
                        "host": host,
                        "port": port,
                        "name": bot_name,
                        "version": bot_version,
                        "connected_at": datetime.now().isoformat(),
                    }

                # Start battle once we have required bots and cool-down is satisfied
                if self._can_start_battle():
                    await self._try_start_battle(trigger="lobby-ready")
                    # Continue listening for next battle
                elif self._is_post_battle_cool_down_active():
                    remaining = self.post_battle_cool_down - (
                        time.monotonic() - self.last_battle_end_time
                    )
                    log.debug(
                        f"Post-battle cool-down active: {remaining:.1f}s remaining"
                    )

            except asyncio.CancelledError:
                log.info("Bot listener cancelled")
                raise
            except RuntimeError as e:
                if "Connection closed" in str(e):
                    log.warning(f"Connection closed, attempting to reconnect...")
                    max_reconnect_attempts = 5
                    reconnect_attempt = 0
                    while reconnect_attempt < max_reconnect_attempts:
                        try:
                            await asyncio.sleep(2)
                            await self.connect()
                            log.info("Reconnected successfully, resuming listener")
                            break  # Successfully reconnected, continue the main while loop
                        except Exception as reconnect_error:
                            reconnect_attempt += 1
                            if reconnect_attempt < max_reconnect_attempts:
                                log.warning(
                                    f"Reconnection attempt {reconnect_attempt}/{max_reconnect_attempts} failed: {reconnect_error}, retrying..."
                                )
                            else:
                                log.error(
                                    f"Failed to reconnect after {max_reconnect_attempts} attempts"
                                )
                                raise RuntimeError(
                                    f"Could not reconnect after {max_reconnect_attempts} attempts"
                                )
                else:
                    log.error(f"WebSocket error: {e}", exc_info=True)
                    raise
            except Exception as e:
                log.error(f"Error listening for bots: {e}", exc_info=True)
                raise

    async def start_battle(self) -> None:
        """Start a battle with connected bots."""
        if self.battle_in_progress:
            log.warning("Battle already in progress")
            return

        if not self._can_start_battle():
            log.warning(f"Not enough bots ({self._selection_requirement_text()})")
            return

        self.battle_in_progress = True
        if not self.first_battle_initiated.is_set():
            self.first_battle_initiated.set()
        start_game_sent = False
        battle_outcome = "unknown"

        try:
            quiet_age = time.monotonic() - self.last_bot_activity
            if (
                self.pre_start_quiet_period > 0
                and quiet_age < self.pre_start_quiet_period
            ):
                wait_time = self.pre_start_quiet_period - quiet_age
                log.info(
                    "Waiting %.2fs quiet period before StartGame (bot list still stabilizing)",
                    wait_time,
                )
                await asyncio.sleep(wait_time)
                # Check if we still have enough bots (without checking battle_in_progress flag)
                if not self._check_bots_still_available():
                    log.warning(
                        "Bot roster changed during quiet period "
                        f"({self._selection_requirement_text()})"
                    )
                    self.battle_in_progress = False
                    return

            # Prepare bot addresses
            bot_addresses = []
            bot_names_ordered = []

            if self._composition_mode_enabled():
                neural_hosts, non_neural_hosts = self._partition_connected_bots()
                selected_neural_hosts = neural_hosts[: self.expected_neural_bots]
                selected_non_neural_hosts = random.sample(
                    non_neural_hosts, self.required_non_neural_bots
                )
                selected_hosts = selected_neural_hosts + selected_non_neural_hosts
                log.info(
                    f"Composition selected: {len(selected_neural_hosts)} neural + "
                    f"{len(selected_non_neural_hosts)} non-neural"
                )
            else:
                selected_hosts = sorted(self.connected_bots.keys())[: self.max_bots]

            for bot_id in selected_hosts:
                bot_info = self.connected_bots[bot_id]
                bot_name = bot_info.get("name", bot_id)
                host = bot_info.get("host", "")
                port = bot_info.get("port")
                if port is None:
                    raise ValueError(
                        f"Bot {bot_name} ({host}) missing port in lobby update"
                    )
                port = int(port)
                bot_addresses.append(BotAddress(host=host, port=port))
                bot_names_ordered.append(bot_name)
                log.info(f"  Including bot: {bot_name} ({host}:{port})")

            # Store mapping from rank to bot address
            # Assuming results are ordered by rank (1, 2, 3, ...)
            for rank, bot_name in enumerate(bot_names_ordered, start=1):
                self.bot_address_map[rank] = bot_name

            log.info(
                f"Starting battle: {len(bot_addresses)} bots, {self.num_rounds} round(s)"
            )

            # Create game setup as dict
            # Scale ready timeout with number of bots: 60s base + 2s per bot
            ready_timeout_ms = max(60000, 60000 + (len(bot_addresses) * 2000))
            game_setup = {
                "gameType": "melee",
                "arenaWidth": self.arena_width,
                "arenaHeight": self.arena_height,
                "minNumberOfParticipants": len(bot_addresses),
                "maxNumberOfParticipants": len(bot_addresses),
                "numberOfRounds": self.num_rounds,
                "gunCoolingRate": 0.1,
                "maxInactivityTurns": self.turns_per_round,
                "turnTimeout": 30000,
                "readyTimeout": ready_timeout_ms,
                "defaultTurnsPerSecond": self.tps,
                "isArenaWidthLocked": False,
                "isArenaHeightLocked": False,
                "isMinNumberOfParticipantsLocked": False,
                "isMaxNumberOfParticipantsLocked": False,
                "isNumberOfRoundsLocked": False,
                "isGunCoolingRateLocked": False,
                "isMaxInactivityTurnsLocked": False,
                "isTurnTimeoutLocked": False,
                "isReadyTimeoutLocked": False,
            }
            log.info(
                f"Ready timeout set to {ready_timeout_ms/1000:.1f}s for {len(bot_addresses)} bots"
            )

            # Create bot addresses as dicts
            bot_address_dicts = [
                {"host": addr.host, "port": addr.port} for addr in bot_addresses
            ]

            # Send StartGame message
            start_msg = {
                "type": "StartGame",
                "botAddresses": bot_address_dicts,
                "gameSetup": game_setup,
            }

            await self._send_message(start_msg)
            start_game_sent = True
            log.info("StartGame message sent, waiting for battle to complete...")

            # Collect events until game ends
            battle_outcome = await self._run_battle_event_loop()

        except Exception as e:
            log.error(f"Error during battle: {e}", exc_info=True)
        finally:
            self.battle_in_progress = False
            # Send StopGame only if battle did not end cleanly
            if start_game_sent and battle_outcome != "ended":
                try:
                    stop_msg = {"type": "StopGame"}
                    await self._send_message(stop_msg)
                except Exception as e:
                    log.error(f"Error sending StopGame: {e}")

    async def _run_battle_event_loop(self) -> str:
        """Process events from a running battle."""
        event_count = 0
        round_count = 0
        # Add timeout to prevent hanging (2 minutes should be enough for any battle event)
        event_timeout = 120.0

        try:
            while True:
                try:
                    msg = await asyncio.wait_for(
                        self._receive_message(), timeout=event_timeout
                    )
                except asyncio.TimeoutError:
                    log.warning(
                        f"No event received for {event_timeout}s - battle may be hung"
                    )
                    return "timeout"

                msg_type = msg.get("type")
                event_count += 1

                if msg_type == "GameStartedEventForObserver":
                    participants = msg.get("participants", [])
                    log.info(f"✓ Battle started with {len(participants)} participants")
                    for p in participants:
                        log.info(f"  - {p.get('name')}")

                elif msg_type == "RoundStartedEvent":
                    round_count += 1
                    log.info(f"  Round {round_count} started")

                elif msg_type == "TickEventForObserver":
                    turn_number = msg.get("turn_number", msg.get("turnNumber"))
                    if (
                        self.tick_log_interval > 0
                        and isinstance(turn_number, int)
                        and turn_number > 0
                        and turn_number % self.tick_log_interval == 0
                    ):
                        log.info(f"  Round {round_count} progress: turn {turn_number}")

                elif msg_type == "RoundEndedEventForObserver":
                    round_num = msg.get(
                        "round_number", msg.get("roundNumber", round_count)
                    )
                    results = msg.get("results", [])
                    log.info(f"  Round {round_num} ended")
                    for res in results:
                        bot_name = res.get("name", res.get("botName", "Unknown"))
                        total_score = self._get_result_value(res, "totalScore", 0)
                        log.info(f"    {bot_name:20} - Score: {total_score}")

                elif msg_type == "GameEndedEventForObserver":
                    log.info("✓ Battle completed!")
                    results = msg.get("results", [])
                    self._log_final_results(results)
                    # Mark battle end time for cool-down period
                    self.last_battle_end_time = time.monotonic()
                    log.info(
                        f"Post-battle cool-down started ({self.post_battle_cool_down:.1f}s) "
                        "to allow simulation cleanup and bot recreation"
                    )
                    return "ended"

                elif msg_type == "GameAbortedEvent":
                    reason = msg.get("message") or msg.get("reason") or "Unknown reason"
                    log.warning(f"✗ Battle aborted! Reason: {reason}")
                    # Log full abort event for debugging
                    log.debug(f"Full GameAbortedEvent: {json.dumps(msg, indent=2)}")
                    self.last_battle_end_time = time.monotonic()
                    log.info(
                        f"Post-abort cool-down started ({self.post_battle_cool_down:.1f}s) "
                        "before next start attempt"
                    )
                    return "aborted"

                else:
                    # Log other messages for debugging
                    if msg_type not in ["TickEventForObserver", "BotMessageEvent"]:
                        log.debug(f"  Event: {msg_type}")

        except asyncio.TimeoutError:
            log.warning("Timeout waiting for battle events")
            return "timeout"
        except Exception as e:
            log.error(f"Error in event loop: {e}", exc_info=True)
            return "error"

        return "unknown"

    def _log_final_results(self, results):
        """Log final battle results in a format simulate.py can parse."""
        log.info("\n" + "=" * 80)
        log.info("FINAL BATTLE RESULTS")
        log.info("=" * 80)

        for res in results:
            rank = self._get_result_value(res, "rank", 0)
            score = self._get_result_value(res, "totalScore", 0)
            damage = self._get_result_value(res, "bulletDamage", 0)
            survival = self._get_result_value(res, "survival", 0)
            kills = self._get_result_value(res, "killBonuses", 0)

            # Prefer stable bot name from result payload
            bot_name = res.get("name", res.get("botName", "Unknown"))
            if bot_name == "Unknown":
                bot_name = self.bot_address_map.get(rank, bot_name)

            # Log in parseable format for simulate.py
            log.info(f"Bot {bot_name} scored {score}")

            # Also log detailed info
            log.debug(
                f"  Rank: {rank}, Score: {score}, Damage: {damage}, Survival: {survival}, Kills: {kills}"
            )

        log.info("=" * 80 + "\n")

    @staticmethod
    def _get_result_value(result: Dict[str, Any], camel_key: str, default: Any) -> Any:
        """Read result value from either camelCase or snake_case key format."""
        if camel_key in result:
            return result[camel_key]

        snake_key = []
        for ch in camel_key:
            if ch.isupper():
                snake_key.append("_")
                snake_key.append(ch.lower())
            else:
                snake_key.append(ch)
        snake_key_str = "".join(snake_key)
        return result.get(snake_key_str, default)

    async def disconnect(self) -> None:
        """Disconnect from server."""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                log.warning(f"Error closing websocket: {e}")
        self.is_connected = False
        log.info("Disconnected from server")

    async def _send_message(self, message) -> None:
        """Send a message to the server."""
        try:
            # Convert message to dict if needed
            if isinstance(message, dict):
                msg_dict = message
                msg_type = message.get("type", "Unknown")
            else:
                # For simple Python classes, use __dict__ directly
                msg_dict = {}
                for k, v in message.__dict__.items():
                    if not k.startswith("_"):
                        # Convert enums to their string value
                        if hasattr(v, "value"):
                            msg_dict[k] = v.value
                        else:
                            msg_dict[k] = v
                msg_type = getattr(message, "type", "Unknown")
                if hasattr(msg_type, "value"):
                    msg_type = msg_type.value

            json_str = json.dumps(msg_dict, default=str)
            log.info(f">>> Sending {msg_type}: {json_str}")
            await self.websocket.send(json_str)
        except Exception as e:
            log.error(f"Error sending message: {e}")
            raise

    async def _receive_message(self) -> Dict[str, Any]:
        """Receive a message from the server."""
        try:
            msg = await self.websocket.recv()
            if isinstance(msg, bytes):
                msg = msg.decode("utf-8")
            return json.loads(msg)
        except websockets.exceptions.ConnectionClosed:
            raise RuntimeError("Connection closed by server")
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON received: {e}")
            raise


async def main():
    """Main entry point."""
    # Get configuration from environment variables
    server_url = os.getenv("SERVER_URL", "ws://tank-royale-server:7654")
    controller_secret = os.getenv("CONTROLLER_SECRET", "7Tr04oRlwlnC84ksjhhzESQ")
    min_bots = int(os.getenv("MIN_BOTS", "2"))
    max_bots = int(os.getenv("MAX_BOTS", "20"))
    num_rounds = int(os.getenv("NUM_ROUNDS", "1"))
    turns_per_round = int(os.getenv("TURNS_PER_ROUND", "300"))
    timeout = int(os.getenv("TIMEOUT", "300"))
    tick_log_interval = int(os.getenv("TICK_LOG_INTERVAL", "100"))
    expected_neural_bots = int(os.getenv("EXPECTED_NEURAL_BOTS", "0"))
    required_non_neural_bots = int(os.getenv("REQUIRED_NON_NEURAL_BOTS", "0"))
    neural_host_prefix = os.getenv("NEURAL_HOST_PREFIX", "neural-bot-")
    pre_start_quiet_period = float(os.getenv("PRE_START_QUIET_PERIOD", "1.5"))
    post_battle_cool_down = float(os.getenv("POST_BATTLE_COOL_DOWN", "10.0"))

    log.info(f"Battle Orchestrator Configuration:")
    log.info(f"  Server: {server_url}")
    log.info(f"  Bots: {min_bots}-{max_bots}")
    log.info(f"  Rounds: {num_rounds}")
    log.info(f"  Timeout: {timeout}s")
    log.info(f"  Tick progress logging: every {tick_log_interval} turn(s)")
    if expected_neural_bots or required_non_neural_bots:
        log.info(
            "  Composition mode: "
            f"{expected_neural_bots} neural + {required_non_neural_bots} non-neural"
        )
    log.info(f"  Pre-start quiet period: {pre_start_quiet_period:.1f}s")
    log.info(f"  Post-battle cool-down: {post_battle_cool_down:.1f}s")

    # Create and run orchestrator
    orchestrator = BattleOrchestrator(
        server_url=server_url,
        controller_secret=controller_secret,
        min_bots=min_bots,
        max_bots=max_bots,
        num_rounds=num_rounds,
        turns_per_round=turns_per_round,
        timeout=timeout,
        tick_log_interval=tick_log_interval,
        expected_neural_bots=expected_neural_bots,
        required_non_neural_bots=required_non_neural_bots,
        neural_host_prefix=neural_host_prefix,
        pre_start_quiet_period=pre_start_quiet_period,
        post_battle_cool_down=post_battle_cool_down,
    )

    await orchestrator.run()


if __name__ == "__main__":
    asyncio.run(main())
