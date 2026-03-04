import os
import random
import sys
from simulate import run_simulation
from evolve import evolve_generation


def get_scores_for_generation(gen_dir, bots_per_sim=10):
    # Validate that bots_per_sim divides evenly into 100 bots
    if 100 % bots_per_sim != 0:
        raise ValueError("bots_per_sim must be divisible into 100 bots evenly")

    num_simulations = 100 // bots_per_sim
    all_scores = {}
    generation_path = os.path.join("generations", gen_dir)
    score_filename = "score.txt"

    # Load persisted scores first so training can resume after failure
    for bot_id in range(1, 101):
        bot_folder = os.path.join(generation_path, f"bot-{bot_id:03d}")
        score_path = os.path.join(bot_folder, score_filename)
        if not os.path.exists(score_path):
            continue

        try:
            with open(score_path, "r", encoding="utf-8") as score_file:
                persisted_score = float(score_file.read().strip())
            all_scores[bot_id] = [persisted_score]
        except (OSError, ValueError):
            # Ignore invalid/corrupted score files and resimulate the bot
            continue

    for sim_idx in range(num_simulations):
        # Chunk bots: sim 0 gets bots 1-10, sim 1 gets 11-20, etc.
        start_bot = sim_idx * bots_per_sim + 1
        end_bot = start_bot + bots_per_sim
        bot_ids = list(range(start_bot, end_bot))

        missing_bot_ids = [bid for bid in bot_ids if bid not in all_scores]
        if not missing_bot_ids:
            continue

        scores = run_simulation(missing_bot_ids, gen_dir)
        for bid, score in scores.items():
            if bid not in all_scores:
                all_scores[bid] = []
            all_scores[bid].append(score)

            # Persist score in bot folder immediately for resumable training
            bot_folder = os.path.join(generation_path, f"bot-{bid:03d}")
            os.makedirs(bot_folder, exist_ok=True)
            score_path = os.path.join(bot_folder, score_filename)
            temp_score_path = f"{score_path}.tmp"
            with open(temp_score_path, "w", encoding="utf-8") as score_file:
                score_file.write(str(float(score)))
            os.replace(temp_score_path, score_path)

    # Average scores
    avg_scores = {bid: sum(scores) / len(scores) for bid, scores in all_scores.items()}
    return avg_scores


def train(num_generations=100):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True, write_through=True)

    # Find the highest generation in the generations folder
    generations_dir = "generations"
    existing_gens = [
        d for d in os.listdir(generations_dir) if d.startswith("generation-")
    ]
    if existing_gens:
        gen_numbers = [int(d.split("-")[1]) for d in existing_gens]
        start_gen = max(gen_numbers)
        current_gen = f"generation-{start_gen}"
    else:
        start_gen = 1
        current_gen = "generation-1"
    for gen in range(start_gen + 1, start_gen + num_generations + 1):
        print(f"Training generation {gen-1}")
        # Get scores
        scores = get_scores_for_generation(current_gen, 20)
        # Evolve
        next_gen = f'generation-{gen}'
        evolve_generation(
            os.path.join("generations", current_gen),
            os.path.join("generations", next_gen),
            scores,
            100,
        )
        current_gen = next_gen


if __name__ == "__main__":
    train()
