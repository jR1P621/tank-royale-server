import os
import onnx
import numpy as np
from onnx import numpy_helper
import random
import shutil
import json


def copy_bot_dir(src_dir, dst_dir):
    """Copy bot directory, excluding score.txt to ensure fresh scoring."""
    os.makedirs(dst_dir, exist_ok=True)
    for item in os.listdir(src_dir):
        if item == "score.txt":
            continue
        src_path = os.path.join(src_dir, item)
        dst_path = os.path.join(dst_dir, item)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)


def load_model(filepath):
    """Load ONNX model from file."""
    try:
        return onnx.load(filepath)
    except Exception as e:
        raise IOError(f"Failed to load model from {filepath}: {e}")

def save_model(model, filepath):
    """Save ONNX model to file."""
    try:
        onnx.save(model, filepath)
    except Exception as e:
        raise IOError(f"Failed to save model to {filepath}: {e}")

def get_weights(model):
    """Extract weights from ONNX model as numpy arrays."""
    weights = {}
    try:
        for init in model.graph.initializer:
            weights[init.name] = numpy_helper.to_array(init)
    except Exception as e:
        raise ValueError(f"Failed to extract weights from model: {e}")
    return weights

def set_weights(model, weights):
    """Set weights in ONNX model from numpy arrays."""
    try:
        for init in model.graph.initializer:
            if init.name in weights:
                target_dtype = numpy_helper.to_array(init).dtype
                value = np.asarray(weights[init.name])
                if value.dtype != target_dtype:
                    value = value.astype(target_dtype, copy=False)
                init.CopyFrom(numpy_helper.from_array(value, init.name))
    except Exception as e:
        raise ValueError(f"Failed to set weights in model: {e}")

def mutate_colors(colors, mutation_rate=0.1):
    """Mutate color values with given mutation rate."""
    new_colors = {}
    for key, rgb in colors.items():
        new_rgb = []
        for c in rgb:
            if random.random() < mutation_rate:
                new_rgb.append(random.randint(0, 255))
            else:
                new_rgb.append(c)
        new_colors[key] = new_rgb
    return new_colors

def mutate_weights(weights, mutation_rate=0.1, mutation_strength=0.1):
    """Mutate neural network weights with given mutation rate and strength."""
    new_weights = {}
    for name, w in weights.items():
        if random.random() < mutation_rate:
            noise = np.random.normal(0, mutation_strength, w.shape).astype(
                w.dtype, copy=False
            )
            new_weights[name] = (w + noise).astype(w.dtype, copy=False)
        else:
            new_weights[name] = w.copy()  # Ensure all weights are included
    return new_weights

def crossover_weights(weights1, weights2):
    """Perform uniform crossover on neural network weights."""
    new_weights = {}
    for name in weights1:
        if name in weights2:
            # Uniform crossover
            mask = np.random.rand(*weights1[name].shape) > 0.5
            target_dtype = weights1[name].dtype
            parent2 = np.asarray(weights2[name]).astype(target_dtype, copy=False)
            new_weights[name] = np.where(mask, weights1[name], parent2).astype(
                target_dtype, copy=False
            )
        else:
            new_weights[name] = weights1[name].copy()
    return new_weights

def crossover_colors(colors1, colors2):
    """Perform uniform crossover on bot colors."""
    new_colors = {}
    for key in colors1:
        if key in colors2:
            rgb1 = np.array(colors1[key])
            rgb2 = np.array(colors2[key])
            mask = np.random.rand(3) > 0.5
            new_rgb = np.where(mask, rgb1, rgb2)
            new_colors[key] = new_rgb.astype(int).tolist()
        else:
            new_colors[key] = (
                colors1[key].copy() if isinstance(colors1[key], list) else colors1[key]
            )
    return new_colors

def evolve_generation(current_gen_dir, next_gen_dir, scores, population_size=100, elite_rate=0.2, crossover_rate=0.4, mutation_rate=0.3, random_rate=0.1):
    """
    Evolve a generation of neural network bots through genetic algorithm.

    Args:
        current_gen_dir: Directory containing current generation bots
        next_gen_dir: Directory to save next generation bots
        scores: Dict mapping bot IDs to fitness scores
        population_size: Total number of bots in generation
        elite_rate, crossover_rate, mutation_rate, random_rate: Distribution percentages
    """
    # Group bots by model_type
    model_types = {}
    for i in range(1, population_size + 1):
        bot_dir = os.path.join(current_gen_dir, f'bot-{i:03d}')
        json_path = os.path.join(bot_dir, 'NeuralBot.json')

        try:
            with open(json_path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load {json_path}: {e}")
            continue

        mt = data.get('modelType', 1)
        if mt not in model_types:
            model_types[mt] = []
        model_types[mt].append(i)

    os.makedirs(next_gen_dir, exist_ok=True)
    template_dir = None
    for i in range(1, population_size + 1):
        potential_template = os.path.join(current_gen_dir, f"bot-{i:03d}")
        if os.path.isdir(potential_template):
            template_dir = potential_template
            break

    if template_dir is None:
        raise ValueError(f"No valid template bot found in {current_gen_dir}")

    bot_index = 1

    for mt, bot_ids in model_types.items():
        group_scores = {bid: scores.get(bid, 0) for bid in bot_ids}
        group_size = len(bot_ids)
        sorted_bots = sorted(group_scores.items(), key=lambda x: x[1], reverse=True)

        elite_count = max(1, int(group_size * 0.3))
        crossover_count = max(1, int(group_size * 0.5))
        mutate_count = max(1, int(group_size * 0.2))
        random_count = group_size - elite_count - crossover_count - mutate_count

        # Elitism
        for i in range(elite_count):
            bot_id, _ = sorted_bots[i]
            src_dir = os.path.join(current_gen_dir, f'bot-{bot_id:03d}')
            dst_dir = os.path.join(next_gen_dir, f'bot-{bot_index:03d}')
            copy_bot_dir(src_dir, dst_dir)

            # Update JSON
            json_path = os.path.join(dst_dir, 'NeuralBot.json')
            try:
                with open(json_path, "r") as f:
                    data = json.load(f)
                data["name"] = f"NeuralBot-{bot_index:03d}"
                with open(json_path, "w") as f:
                    json.dump(data, f, indent=2)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Warning: Could not update {json_path}: {e}")

            bot_index += 1

        # Crossover
        for i in range(crossover_count):
            parent1_id, _ = random.choice(sorted_bots[:max(1, len(sorted_bots)//2)])
            parent2_id, _ = random.choice(sorted_bots[:max(1, len(sorted_bots)//2)])
            src1_dir = os.path.join(current_gen_dir, f'bot-{parent1_id:03d}')
            src2_dir = os.path.join(current_gen_dir, f'bot-{parent2_id:03d}')
            dst_dir = os.path.join(next_gen_dir, f'bot-{bot_index:03d}')
            copy_bot_dir(src1_dir, dst_dir)

            try:
                model = load_model(os.path.join(src1_dir, "model.onnx"))
                weights1 = get_weights(model)
                weights2 = get_weights(load_model(os.path.join(src2_dir, "model.onnx")))
                new_weights = crossover_weights(weights1, weights2)
                set_weights(model, new_weights)
                save_model(model, os.path.join(dst_dir, "model.onnx"))
            except Exception as e:
                print(f"Warning: Could not crossover models: {e}")

            # Crossover colors from config.json
            config1_path = os.path.join(src1_dir, "config.json")
            config2_path = os.path.join(src2_dir, "config.json")

            try:
                with open(config1_path, "r") as f:
                    config1 = json.load(f)
                with open(config2_path, "r") as f:
                    config2 = json.load(f)

                colors1 = config1.get("colors", {})
                colors2 = config2.get("colors", {})
                new_colors = crossover_colors(colors1, colors2)
                config1["colors"] = new_colors

                with open(os.path.join(dst_dir, "config.json"), "w") as f:
                    json.dump(config1, f, indent=2)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Warning: Could not crossover colors from config: {e}")

            # Update JSON
            json_path = os.path.join(dst_dir, 'NeuralBot.json')
            try:
                with open(json_path, "r") as f:
                    data = json.load(f)
                data["name"] = f"NeuralBot-{bot_index:03d}"
                with open(json_path, "w") as f:
                    json.dump(data, f, indent=2)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Warning: Could not update {json_path}: {e}")

            bot_index += 1

        # Mutation
        for i in range(mutate_count):
            parent_id, _ = random.choice(sorted_bots[:max(1, len(sorted_bots)//2)])
            src_dir = os.path.join(current_gen_dir, f'bot-{parent_id:03d}')
            dst_dir = os.path.join(next_gen_dir, f'bot-{bot_index:03d}')
            copy_bot_dir(src_dir, dst_dir)

            try:
                model = load_model(os.path.join(src_dir, "model.onnx"))
                weights = get_weights(model)
                new_weights = mutate_weights(weights)
                set_weights(model, new_weights)
                save_model(model, os.path.join(dst_dir, "model.onnx"))
            except Exception as e:
                print(f"Warning: Could not mutate model: {e}")

            # Mutate colors from config.json
            config_path = os.path.join(dst_dir, "config.json")
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)

                colors = config.get("colors", {})
                new_colors = mutate_colors(colors)
                config["colors"] = new_colors

                with open(config_path, "w") as f:
                    json.dump(config, f, indent=2)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Warning: Could not mutate colors from config: {e}")

            # Update JSON
            json_path = os.path.join(dst_dir, 'NeuralBot.json')
            try:
                with open(json_path, "r") as f:
                    data = json.load(f)
                data["name"] = f"NeuralBot-{bot_index:03d}"
                with open(json_path, "w") as f:
                    json.dump(data, f, indent=2)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Warning: Could not update {json_path}: {e}")

            bot_index += 1

        # Random
        for i in range(random_count):
            dst_dir = os.path.join(next_gen_dir, f'bot-{bot_index:03d}')
            copy_bot_dir(template_dir, dst_dir)

            try:
                # Generate new random model of same type
                from generate_model import create_random_nn_onnx

                create_random_nn_onnx(mt, filename=os.path.join(dst_dir, "model.onnx"))
            except Exception as e:
                print(f"Warning: Could not generate random model: {e}")

            # Generate random colors in config.json
            colors = {
                "bodyColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)],
                "turretColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)],
                "radarColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)],
                "bulletColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)],
                "scanColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
            }

            config_path = os.path.join(dst_dir, "config.json")
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                config["colors"] = colors
                with open(config_path, "w") as f:
                    json.dump(config, f, indent=2)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Warning: Could not update config.json: {e}")

            # Update JSON
            json_path = os.path.join(dst_dir, 'NeuralBot.json')
            try:
                with open(json_path, "r") as f:
                    data = json.load(f)
                data["name"] = f"NeuralBot-{bot_index:03d}"
                data["modelType"] = mt
                with open(json_path, "w") as f:
                    json.dump(data, f, indent=2)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Warning: Could not update {json_path}: {e}")

            bot_index += 1

if __name__ == "__main__":
    # Example usage
    scores = {i: random.random() for i in range(1, 101)}  # Dummy scores
    evolve_generation('../generation-1', '../generation-2', scores)
