import os
import onnx
import numpy as np
from onnx import numpy_helper
import random
import shutil
import json

def load_model(filepath):
    return onnx.load(filepath)

def save_model(model, filepath):
    onnx.save(model, filepath)

def get_weights(model):
    weights = {}
    for init in model.graph.initializer:
        weights[init.name] = numpy_helper.to_array(init)
    return weights

def set_weights(model, weights):
    for init in model.graph.initializer:
        if init.name in weights:
            init.CopyFrom(numpy_helper.from_array(weights[init.name], init.name))

def mutate_colors(colors, mutation_rate=0.1):
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
    new_weights = {}
    for name, w in weights.items():
        if random.random() < mutation_rate:
            noise = np.random.normal(0, mutation_strength, w.shape)
            new_weights[name] = w + noise
        else:
            new_weights[name] = w
    return new_weights

def crossover_weights(weights1, weights2):
    new_weights = {}
    for name in weights1:
        if name in weights2:
            # Uniform crossover
            mask = np.random.rand(*weights1[name].shape) > 0.5
            new_weights[name] = np.where(mask, weights1[name], weights2[name])
        else:
            new_weights[name] = weights1[name]
    return new_weights

def crossover_colors(colors1, colors2):
    new_colors = {}
    for key in colors1:
        if key in colors2:
            rgb1 = np.array(colors1[key])
            rgb2 = np.array(colors2[key])
            mask = np.random.rand(3) > 0.5
            new_rgb = np.where(mask, rgb1, rgb2)
            new_colors[key] = new_rgb.tolist()
        else:
            new_colors[key] = colors1[key]
    return new_colors

def evolve_generation(current_gen_dir, next_gen_dir, scores, population_size=100, elite_rate=0.2, crossover_rate=0.4, mutation_rate=0.3, random_rate=0.1):
    # Group bots by model_type
    model_types = {}
    for i in range(1, population_size + 1):
        bot_dir = os.path.join(current_gen_dir, f'bot-{i:03d}')
        json_path = os.path.join(bot_dir, 'NeuralBot.json')
        with open(json_path, 'r') as f:
            data = json.load(f)
        mt = data.get('modelType', 1)
        if mt not in model_types:
            model_types[mt] = []
        model_types[mt].append(i)
    
    os.makedirs(next_gen_dir, exist_ok=True)
    template_dir = os.path.join(current_gen_dir, 'bot-001')
    
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
            shutil.copytree(src_dir, dst_dir)
            # Update JSON
            json_path = os.path.join(dst_dir, 'NeuralBot.json')
            with open(json_path, 'r') as f:
                data = json.load(f)
            data['name'] = f'NeuralBot-{bot_index:03d}'
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)
            bot_index += 1
        
        # Crossover
        for i in range(crossover_count):
            parent1_id, _ = random.choice(sorted_bots[:max(1, len(sorted_bots)//2)])
            parent2_id, _ = random.choice(sorted_bots[:max(1, len(sorted_bots)//2)])
            src1_dir = os.path.join(current_gen_dir, f'bot-{parent1_id:03d}')
            src2_dir = os.path.join(current_gen_dir, f'bot-{parent2_id:03d}')
            dst_dir = os.path.join(next_gen_dir, f'bot-{bot_index:03d}')
            shutil.copytree(src1_dir, dst_dir)
            
            model = load_model(os.path.join(src1_dir, 'model.onnx'))
            weights1 = get_weights(model)
            weights2 = get_weights(load_model(os.path.join(src2_dir, 'model.onnx')))
            new_weights = crossover_weights(weights1, weights2)
            set_weights(model, new_weights)
            save_model(model, os.path.join(dst_dir, 'model.onnx'))
            
            # Crossover colors
            colors1_path = os.path.join(src1_dir, 'colors.json')
            colors2_path = os.path.join(src2_dir, 'colors.json')
            with open(colors1_path, 'r') as f:
                colors1 = json.load(f)
            with open(colors2_path, 'r') as f:
                colors2 = json.load(f)
            new_colors = crossover_colors(colors1, colors2)
            with open(os.path.join(dst_dir, 'colors.json'), 'w') as f:
                json.dump(new_colors, f)
            
            # Update JSON
            json_path = os.path.join(dst_dir, 'NeuralBot.json')
            with open(json_path, 'r') as f:
                data = json.load(f)
            data['name'] = f'NeuralBot-{bot_index:03d}'
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)
            bot_index += 1
        
        # Mutation
        for i in range(mutate_count):
            parent_id, _ = random.choice(sorted_bots[:max(1, len(sorted_bots)//2)])
            src_dir = os.path.join(current_gen_dir, f'bot-{parent_id:03d}')
            dst_dir = os.path.join(next_gen_dir, f'bot-{bot_index:03d}')
            shutil.copytree(src_dir, dst_dir)
            
            model = load_model(os.path.join(src_dir, 'model.onnx'))
            weights = get_weights(model)
            new_weights = mutate_weights(weights)
            set_weights(model, new_weights)
            save_model(model, os.path.join(dst_dir, 'model.onnx'))
            
            # Mutate colors
            colors_path = os.path.join(dst_dir, 'colors.json')
            with open(colors_path, 'r') as f:
                colors = json.load(f)
            new_colors = mutate_colors(colors)
            with open(colors_path, 'w') as f:
                json.dump(new_colors, f)
            
            # Update JSON
            json_path = os.path.join(dst_dir, 'NeuralBot.json')
            with open(json_path, 'r') as f:
                data = json.load(f)
            data['name'] = f'NeuralBot-{bot_index:03d}'
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)
            bot_index += 1
        
        # Random
        for i in range(random_count):
            dst_dir = os.path.join(next_gen_dir, f'bot-{bot_index:03d}')
            shutil.copytree(template_dir, dst_dir)
            
            # Generate new random model of same type
            from generate_model import create_random_nn_onnx
            create_random_nn_onnx(mt, filename=os.path.join(dst_dir, 'model.onnx'))
            
            # Generate random colors
            colors = {
                "bodyColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)],
                "turretColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)],
                "radarColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)],
                "bulletColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)],
                "scanColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
            }
            with open(os.path.join(dst_dir, 'colors.json'), 'w') as f:
                json.dump(colors, f)
            
            # Update JSON
            json_path = os.path.join(dst_dir, 'NeuralBot.json')
            with open(json_path, 'r') as f:
                data = json.load(f)
            data['name'] = f'NeuralBot-{bot_index:03d}'
            data['modelType'] = mt
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)
            bot_index += 1

if __name__ == "__main__":
    # Example usage
    scores = {i: random.random() for i in range(1, 101)}  # Dummy scores
    evolve_generation('../generation-1', '../generation-2', scores)