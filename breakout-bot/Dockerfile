FROM mcr.microsoft.com/dotnet/sdk:10.0
WORKDIR /app

COPY BreakoutBot.cs .
COPY BreakoutBot.json .

ENTRYPOINT ["dotnet", "run", "BreakoutBot.cs"]
