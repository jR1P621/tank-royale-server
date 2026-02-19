import os
import shutil
from generate_model import create_random_nn_onnx
import json
import random

def generate_random_colors():
    return {
        "bodyColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)],
        "turretColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)],
        "radarColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)],
        "bulletColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)],
        "scanColor": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
    }

def generate_batch(generation_dir, num_bots=100):
    os.makedirs(generation_dir, exist_ok=True)
    
    for i in range(1, num_bots + 1):
        bot_dir = os.path.join(generation_dir, f'bot-{i:03d}')
        os.makedirs(bot_dir, exist_ok=True)
        
        model_type = ((i - 1) // 10) + 1  # 10 bots per type
        
        # Copy shared files
        shutil.copy('../shared/NeuralBot.cs', bot_dir)
        shutil.copy('../shared/NeuralBot.json', bot_dir)
        shutil.copy('../shared/NeuralBot.csproj', bot_dir)
        shutil.copy('../shared/Dockerfile', bot_dir)
        
        # Generate unique model
        model_path = os.path.join(bot_dir, 'model.onnx')
        create_random_nn_onnx(model_type, filename=model_path)
        
        # Generate random colors
        colors = generate_random_colors()
        with open(os.path.join(bot_dir, 'colors.json'), 'w') as f:
            json.dump(colors, f)
        
        # Update JSON name and model type
        json_path = os.path.join(bot_dir, 'NeuralBot.json')
        with open(json_path, 'r') as f:
            data = json.load(f)
        data['name'] = f'NeuralBot-{i:03d}'
        data['modelType'] = model_type
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    generate_batch('../generation-1', 100)