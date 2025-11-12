# Tank Royale Server

## Quick Start

```bash
docker compose up --build
```

Server runs on ws://localhost:7654

## Services

Run all services:
```bash
docker compose up --build
```

Run only the server:
```bash
docker compose up --build tank-royale-server
```

Run server + sample bots:
```bash
docker compose up --build tank-royale-server sample-bots
```

Run server + example bot:
```bash
docker compose up --build tank-royale-server example-bot
```

Run only the example bot:
```bash
docker compose up --build example-bot
```

## Override Environment Variables

Create `docker-compose.override.yml`:

```yaml
services:
  tank-royale-server:
    environment:
      CONTROLLER_SECRET: my-controller-secret
      BOT_SECRET: my-bot-secret
      PORT: 7654

  sample-bots:
    environment:
      SERVER_URL: ws://tank-royale-server:7654
      SERVER_SECRET: my-bot-secret
      BOTS: Crazy,Fire,SpinBot

  example-bot:
    environment:
      SERVER_URL: ws://tank-royale-server:7654
      SERVER_SECRET: my-bot-secret
```
