FROM mcr.microsoft.com/dotnet/sdk:10.0
WORKDIR /app

COPY BreakoutBot.cs .
COPY BreakoutBot.json .

ENTRYPOINT ["sh", "-c", "SERVER_URL=\"$SERVER_URL\" SERVER_SECRET=\"$SERVER_SECRET\" dotnet run BreakoutBot.cs"]
