FROM mcr.microsoft.com/dotnet/sdk:8.0

ARG BOTS_VERSION=0.34.1
ARG BOTS_URL=https://github.com/robocode-dev/tank-royale/releases/download/v${BOTS_VERSION}/sample-bots-csharp-${BOTS_VERSION}.zip

RUN apt-get update && apt-get install -y unzip curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN curl -L -o sample-bots.zip ${BOTS_URL} && \
    unzip sample-bots.zip -d /app/bots && \
    rm sample-bots.zip

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV SERVER_URL=ws://tank-royale-server:7654
ENV SERVER_SECRET=
ENV BOTS=Crazy

ENTRYPOINT ["/app/entrypoint.sh"]
