import onnx
from onnx import helper, TensorProto
import numpy as np

def create_random_nn_onnx(model_type=1, filename="model.onnx"):
    # Model types: 1-3: basic (12 in), 4-10: bullet (27 in)
    input_size = 12 if model_type <= 3 else 27
    if model_type == 1:
        hidden_size = 32
    elif model_type in [2,4]:
        hidden_size = 64
    elif model_type in [3,5]:
        hidden_size = 128
    elif model_type == 6:
        hidden_size = 256
    elif model_type == 7:
        hidden_size = 128  # Multi, but keep simple
    elif model_type == 8:
        hidden_size = 512
    elif model_type == 9:
        hidden_size = 64  # Deep, but 2 layers
    else:  # 10
        hidden_size = 256
    output_size = 4

    # Define nodes
    input_tensor = helper.make_tensor_value_info('input', TensorProto.FLOAT, [1, input_size])
    output_tensor = helper.make_tensor_value_info('output', TensorProto.FLOAT, [1, output_size])

    # Random weights
    w1 = np.random.randn(input_size, hidden_size).astype(np.float32)
    b1 = np.random.randn(hidden_size).astype(np.float32)
    w2 = np.random.randn(hidden_size, output_size).astype(np.float32)
    b2 = np.random.randn(output_size).astype(np.float32)

    # Create initializers
    w1_init = helper.make_tensor('w1', TensorProto.FLOAT, w1.shape, w1.flatten())
    b1_init = helper.make_tensor('b1', TensorProto.FLOAT, b1.shape, b1.flatten())
    w2_init = helper.make_tensor('w2', TensorProto.FLOAT, w2.shape, w2.flatten())
    b2_init = helper.make_tensor('b2', TensorProto.FLOAT, b2.shape, b2.flatten())

    # Nodes
    node1 = helper.make_node('MatMul', ['input', 'w1'], ['matmul1_out'])
    node2 = helper.make_node('Add', ['matmul1_out', 'b1'], ['add1_out'])
    node3 = helper.make_node('Relu', ['add1_out'], ['relu_out'])
    node4 = helper.make_node('MatMul', ['relu_out', 'w2'], ['matmul2_out'])
    node5 = helper.make_node('Add', ['matmul2_out', 'b2'], ['output'])

    # Graph
    graph = helper.make_graph(
        [node1, node2, node3, node4, node5],
        'nn_model',
        [input_tensor],
        [output_tensor],
        [w1_init, b1_init, w2_init, b2_init]
    )

    # Model
    model = helper.make_model(graph, producer_name='onnx-example')
    onnx.save(model, filename)

if __name__ == "__main__":
    create_random_nn_onnx()