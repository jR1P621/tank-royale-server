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

        # Copy all shared source files into the bot directory
        shutil.copy('../shared/Dockerfile', bot_dir)
        shutil.copy('../shared/NeuralBot.cs', bot_dir)
        shutil.copy('../shared/NeuralBot.csproj', bot_dir)
        shutil.copy('../shared/NeuralBot.json', bot_dir)

        # Ensure config.json is generated and placed in the bot directory
        config_path = os.path.join(bot_dir, 'config.json')
        model_type = ((i - 1) // 10) + 1  # 10 bots per type

        # Generate unique model
        model_path = os.path.join(bot_dir, 'model.onnx')
        create_random_nn_onnx(model_type, filename=model_path)

        # Define model-specific input tensor info based on model_type
        if model_type in [1, 2, 3]:
            input_tensor_info = {
                "includeBullets": False,  # Models 1-3 have input_size 12, no bullet data
                "includeEnemy": True,
                "includeRadar": False
            }
        else:  # model_type 4-10
            input_tensor_info = {
                "includeBullets": True,  # Models 4-10 have input_size 27, include bullet data
                "includeEnemy": True,
                "includeRadar": True
            }

        # Generate random colors
        colors = generate_random_colors()

        # Combine into config.json
        config = {
            "colors": colors,
            "inputTensorInfo": input_tensor_info
        }

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

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