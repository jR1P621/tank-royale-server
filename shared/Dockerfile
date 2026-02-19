FROM mcr.microsoft.com/dotnet/sdk:10.0
WORKDIR /app

COPY NeuralBot.csproj .
COPY NeuralBot.cs .
COPY NeuralBot.json .
COPY config.json .
COPY model.onnx .

RUN dotnet restore
RUN dotnet build -c Release

ENTRYPOINT ["dotnet", "run", "--project", "NeuralBot.csproj"]