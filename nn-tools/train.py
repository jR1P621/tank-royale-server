import os
import random
from simulate import run_simulation
from evolve import evolve_generation

def get_scores_for_generation(gen_dir, num_simulations=10, bots_per_sim=10):
    all_scores = {}
    for _ in range(num_simulations):
        # Select random bots
        bot_ids = random.sample(range(1, 101), bots_per_sim)
        scores = run_simulation(bot_ids, gen_dir)
        for bid, score in scores.items():
            if bid not in all_scores:
                all_scores[bid] = []
            all_scores[bid].append(score)
    
    # Average scores
    avg_scores = {bid: sum(scores) / len(scores) for bid, scores in all_scores.items()}
    return avg_scores

def train(num_generations=5):
    current_gen = 'generation-1'
    for gen in range(2, num_generations + 2):
        print(f"Training generation {gen-1}")
        # Get scores
        scores = get_scores_for_generation(current_gen)
        # Evolve
        next_gen = f'generation-{gen}'
        evolve_generation(current_gen, next_gen, scores)
        current_gen = next_gen

if __name__ == "__main__":
    train()