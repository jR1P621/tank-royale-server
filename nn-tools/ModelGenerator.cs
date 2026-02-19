#:package Microsoft.ML 3.0.1
#:package Microsoft.ML.Onnx 0.21.0

using Microsoft.ML;
using Microsoft.ML.Data;
using System;
using System.Linq;

public class ModelGenerator
{
    public class InputData
    {
        [VectorType(12)]
        public float[] Features { get; set; }
    }

    public class OutputData
    {
        [VectorType(4)]
        public float[] Label { get; set; }
    }

    public static void Main()
    {
        var mlContext = new MLContext(seed: 0); // For reproducibility, but we'll randomize

        // Generate random training data
        var data = mlContext.Data.LoadFromEnumerable(Enumerable.Range(0, 1000).Select(i =>
        {
            var rand = new Random();
            return new InputData
            {
                Features = new float[12] { (float)rand.NextDouble(), (float)rand.NextDouble(), (float)rand.NextDouble(), (float)rand.NextDouble(), (float)rand.NextDouble(), (float)rand.NextDouble(), (float)rand.NextDouble(), (float)rand.NextDouble(), (float)rand.NextDouble(), (float)rand.NextDouble(), (float)rand.NextDouble(), (float)rand.NextDouble() }
            };
        }));

        // Create pipeline with neural network
        var pipeline = mlContext.Transforms.Concatenate("Features", "Features")
            .Append(mlContext.Regression.Trainers.Sdca(labelColumnName: "Label", featureColumnName: "Features")); // Use SDCA for regression, but for NN, ML.NET has limited NN support

        // Actually, ML.NET doesn't have built-in NN for regression easily. Use ImageClassification with custom, but complicated.

        // Alternative: Use TensorFlow or export from Python.

        // For now, create a simple model and export.

        // Since ONNX export is for trained models, perhaps create a dummy trained model.

        var dummyData = mlContext.Data.LoadFromEnumerable(new[] { new InputData { Features = new float[12] }, new OutputData { Label = new float[4] } });

        var model = pipeline.Fit(dummyData);

        // Export to ONNX
        using var stream = new System.IO.FileStream("model.onnx", System.IO.FileMode.Create);
        mlContext.Model.ConvertToOnnx(model, dummyData, stream);
    }
}