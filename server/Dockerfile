FROM eclipse-temurin:21-jre-alpine

ARG TANKROYALE_VERSION=0.34.1
ARG JAR_URL=https://github.com/robocode-dev/tank-royale/releases/download/v${TANKROYALE_VERSION}/robocode-tankroyale-server-${TANKROYALE_VERSION}.jar

RUN apk add --no-cache curl

WORKDIR /app

RUN curl -L -o robocode-tankroyale-server.jar ${JAR_URL}

EXPOSE 7654

ENV CONTROLLER_SECRET=controller-secret-change-me
ENV BOT_SECRET=bot-secret-change-me
ENV PORT=7654

CMD ["sh", "-c", "java -jar robocode-tankroyale-server.jar --port=${PORT} --controller-secrets=${CONTROLLER_SECRET} --bot-secrets=${BOT_SECRET}"]
