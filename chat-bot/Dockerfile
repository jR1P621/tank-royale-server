FROM mcr.microsoft.com/dotnet/sdk:10.0
WORKDIR /app

COPY ChatBot.cs .
COPY ChatBot.json .

ENTRYPOINT ["sh", "-c", "SERVER_URL=\"$SERVER_URL\" SERVER_SECRET=\"$SERVER_SECRET\" dotnet run ChatBot.cs"]
