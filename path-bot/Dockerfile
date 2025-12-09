FROM mcr.microsoft.com/dotnet/sdk:10.0
WORKDIR /app

COPY PathBot.cs .
COPY PathBot.json .

ENTRYPOINT ["dotnet", "run", "PathBot.cs"]
