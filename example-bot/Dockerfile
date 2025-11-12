FROM mcr.microsoft.com/dotnet/sdk:10.0
WORKDIR /app

COPY ExampleBot.cs .
COPY ExampleBot.json .

ENTRYPOINT ["dotnet", "run", "ExampleBot.cs"]
