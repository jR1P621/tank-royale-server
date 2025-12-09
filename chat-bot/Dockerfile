FROM mcr.microsoft.com/dotnet/sdk:10.0
WORKDIR /app

COPY ChatBot.cs .
COPY ChatBot.json .

ENTRYPOINT ["dotnet", "run", "ChatBot.cs"]
