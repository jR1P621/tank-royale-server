FROM mcr.microsoft.com/dotnet/sdk:10.0
WORKDIR /app

COPY ExampleBot.cs .
COPY ExampleBot.json .

ENTRYPOINT ["sh", "-c", "SERVER_URL=\"$SERVER_URL\" SERVER_SECRET=\"$SERVER_SECRET\" dotnet run ExampleBot.cs"]
