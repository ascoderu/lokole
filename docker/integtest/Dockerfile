FROM microsoft/azure-cli:2.0.32

RUN apk add -q --no-cache \
    curl=7.59.0-r0 \
    docker=1.11.2-r1 \
    jq=1.5-r2 \
    util-linux=2.28-r3

RUN pip3 install --no-cache-dir --upgrade pip==19.2.3 && \
  pip3 install --no-cache-dir httpie==1.0.2

WORKDIR /app

COPY .env .
COPY docker/integtest/ ./

CMD ["./tests.sh"]
