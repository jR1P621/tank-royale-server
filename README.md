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

## Manual Non-Neural Bot Startup

Use the helper script to start persistent non-neural bot containers before running neural simulations:

```bash
python .\nn-tools\start_non_neural_bots.py start
```

By default, this starts only non-neural bot services (`--no-deps`) so existing
`tank-royale-server` and `battle-controller` containers are not recreated.
Use `--with-deps` if you explicitly want dependencies started too.

Check status:

```bash
python .\nn-tools\start_non_neural_bots.py status
```

Stop only non-neural bot services:

```bash
python .\nn-tools\start_non_neural_bots.py stop
```

## Neural Bot (Python shared template)

The shared neural bot template in [shared](shared) now runs on Python and is used by `nn-tools/generate_batch.py` when creating generation bots.

Runtime dependencies for generated neural bots are defined in `shared/requirements.txt`:

- `robocode-tankroyale-bot-api`
- `onnxruntime`
- `numpy`

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
