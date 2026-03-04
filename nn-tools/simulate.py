import subprocess
import time
import os
import re
import sys
import threading
import queue
from datetime import datetime, timezone


def run_docker_compose_with_retry(compose_cmd, max_retries=3):
    """
    Run docker compose up with exponential backoff on buildkit snapshot errors.

    Args:
        compose_cmd: List of command arguments for docker compose
        max_retries: Maximum number of retry attempts

    Returns:
        The completed process result

    Raises:
        subprocess.CalledProcessError: If all retries are exhausted
    """
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                compose_cmd, check=True, capture_output=True, text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            # Check if this is a buildkit snapshot extraction error
            error_output = e.stderr + e.stdout
            if "snapshot" in error_output.lower() and attempt < max_retries - 1:
                wait_time = 2**attempt  # 1s, 2s, 4s
                print(f"\n⚠️  Docker buildkit snapshot error detected.")
                print(
                    f"Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...\n"
                )
                time.sleep(wait_time)
            else:
                # Not a snapshot error, or last attempt - raise it
                raise


def run_simulation(bot_ids, generation_dir, simulation_seconds=600, include_deps=False):
    """
    Run a simulation with selected neural bots.

    Assumes both Tank Royale server and battle-controller are already running.
    Start them once with: docker compose up tank-royale-server battle-controller -d

    Args:
        bot_ids: List of bot IDs to include in the simulation (e.g., [1, 2, 3])
        generation_dir: Generation directory (e.g., "generation-1")
        simulation_seconds: Maximum time to wait for simulation to complete
        include_deps: If True, allow docker compose to start dependencies

    Returns:
        Dictionary of {bot_id: score} for bots that completed
    """
    compose_file = os.path.join("./docker-compose.yml")

    # Read original docker-compose.yml
    with open(compose_file, "r") as f:
        original_content = f.read()

    # Remove existing neural-bot services
    content = re.sub(
        r"  neural-bot-\d+:\n.*?(?=\n\n|\n  [a-z]|\Z)",
        "",
        original_content,
        flags=re.DOTALL,
    )

    # Add selected bots
    services = ""
    for bid in bot_ids:
        services += f"""
  neural-bot-{bid:03d}:
    build:
      context: ./generations/{generation_dir}/bot-{bid:03d}
      dockerfile: Dockerfile
    container_name: neural-bot-{bid:03d}
    environment:
      SERVER_URL: ws://tank-royale-server:7654
      SERVER_SECRET: j1etPtYUMVuCWGUlW6hF6AV
    depends_on:
      - tank-royale-server
      - battle-controller
    restart: unless-stopped
    """

    # Insert before the end
    content = content.rstrip() + services + "\n"

    # Write modified docker-compose.yml
    with open(compose_file, "w") as f:
        f.write(content)

    try:
        # Run docker compose (server should already be running separately)
        CONTAINER_RUNTIME = os.getenv("CONTAINER_RUNTIME", "docker")

        print(
            f"Starting simulation with {len(bot_ids)} bots for {simulation_seconds}s..."
        )
        print("(Ensure server + controller are running:")
        print("  docker compose up tank-royale-server battle-controller -d)")

        # Clear logs to avoid mixing with previous simulation results
        subprocess.run(
            [CONTAINER_RUNTIME, "compose", "logs", "--tail", "0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        compose_up_cmd = [CONTAINER_RUNTIME, "compose", "up", "--build", "-d"]
        if not include_deps:
            compose_up_cmd.append("--no-deps")
        compose_up_cmd += [f"neural-bot-{bid:03d}" for bid in bot_ids]
        run_docker_compose_with_retry(compose_up_cmd)

        # Wait for logs and monitor battle progress (include battle-controller and neural bots)
        logs_since = datetime.now(timezone.utc).isoformat()
        bot_service_names = [f"neural-bot-{bid:03d}" for bid in bot_ids]
        proc = subprocess.Popen(
            [
                CONTAINER_RUNTIME,
                "compose",
                "logs",
                "-f",
                "--tail",
                "0",
                "--since",
                logs_since,
                "battle-controller",
            ]
            # + bot_service_names
            ,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Use a queue to handle non-blocking reads with timeout
        line_queue = queue.Queue()

        def read_output():
            """Read lines from process in background thread."""
            try:
                while True:
                    line = proc.stdout.readline()
                    if line:
                        line_queue.put(line)
                    else:
                        break
            except:
                pass

        reader_thread = threading.Thread(target=read_output, daemon=True)
        reader_thread.start()

        lines = []
        start_time = time.time()
        game_ended = False
        game_ended_at = None
        initial_wait = True  # Wait for first bot to be ready

        while True:
            # Try to get a line with timeout instead of blocking indefinitely
            try:
                line = line_queue.get(timeout=2.0)  # 2 second timeout on queue reads
            except queue.Empty:
                line = ""  # Timeout - no new output

            if line:
                print(line, end="")  # realtime console output
                lines.append(line)  # keep for parsing

                # Count occurrences of FINAL BATTLE RESULTS
                if "FINAL BATTLE RESULTS" in line:
                    if initial_wait:
                        # First battle detected
                        game_ended = True
                        game_ended_at = time.time()
                        initial_wait = False

            # Stop if we've been running for too long or game ended with sufficient wait
            elapsed = time.time() - start_time
            if elapsed >= simulation_seconds:
                break

            # Once game has ended, wait a bit longer to ensure all logs are captured
            if game_ended and game_ended_at and (time.time() - game_ended_at) > 5:
                break

            # Check if process has exited
            if proc.poll() is not None:
                # Process exited, drain any remaining lines from queue
                try:
                    while True:
                        line = line_queue.get_nowait()
                        if line:
                            print(line, end="")
                            lines.append(line)
                except queue.Empty:
                    pass
                break

        print(f"\nSimulation completed in {time.time() - start_time:.1f}s")

        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

        # Get logs from battle-controller and neural bots
        result = subprocess.run(
            [
                CONTAINER_RUNTIME,
                "compose",
                "logs",
                "--since",
                logs_since,
                "battle-controller",
            ]
            + bot_service_names,
            capture_output=True,
            text=True,
        )
        logs = result.stdout

        # Parse scores from logs
        # Accepted formats from orchestrator:
        #   "Bot neural-bot-001 scored 50"
        #   "Bot NeuralBot-001 scored 50"
        #   "Bot NeuralBot-020 scored 500"
        scores = {}
        for line in logs.split("\n"):
            # Updated regex to handle robot names with hyphens and variable digit counts
            match = re.search(
                r"Bot\s+(?:neural-bot-|NeuralBot-)(\d+)\s+scored\s+(\d+)", line
            )
            if match:
                bid = int(match.group(1))
                score = int(match.group(2))
                # Only overwrite if this is a later result (in case of multiple runs in logs)
                if bid not in scores or score > scores[bid]:
                    scores[bid] = score
                    print(f"  Bot {bid:03d}: score = {score}")

        if not scores:
            print(f"\nWarning: No scores found in logs! Battle may not have completed.")
            print(f"Check logs above for issues.")

        return scores

    finally:
        # Stop only neural bots (preserve server and controller)
        print("\nCleaning up neural bots...")
        CONTAINER_RUNTIME = os.getenv("CONTAINER_RUNTIME", "docker")

        # Remove only neural bot containers (preserve server and controller)
        containers_to_remove = [f"neural-bot-{bid:03d}" for bid in bot_ids]
        subprocess.run(
            [CONTAINER_RUNTIME, "rm", "-f"] + containers_to_remove,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Restore original docker-compose.yml
        with open(compose_file, "w") as f:
            f.write(original_content)


if __name__ == "__main__":
    # Example: simulate generation 1 with N bots
    N = 20
    bot_ids = [i for i in range(1, N + 1)]
    generation = "generation-1"

    # Allow command line arguments
    if len(sys.argv) > 1:
        generation = sys.argv[1]
    if len(sys.argv) > 2:
        bot_ids = [int(x) for x in sys.argv[2].split(",")]
    include_deps = "--with-deps" in sys.argv

    print(f"Running simulation: {generation} with bots {bot_ids}")
    scores = run_simulation(
        bot_ids,
        generation,
        simulation_seconds=600,
        include_deps=include_deps,
    )
    print(f"\nFinal scores: {scores}")
