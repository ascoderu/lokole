ARG NODE_VERSION=12
FROM node:${NODE_VERSION} AS builder

WORKDIR /app/opwen_statuspage
COPY ./opwen_statuspage/package*.json ./
RUN npm install

COPY ./opwen_statuspage ./
RUN npm run ci

FROM builder AS compiler

RUN npm run build

FROM node:${NODE_VERSION} AS runtime

RUN npm install -g serve@11.3.0

WORKDIR /app

COPY --from=compiler /app/opwen_statuspage/build ./lokole/

CMD ["serve", "-n", "."]
