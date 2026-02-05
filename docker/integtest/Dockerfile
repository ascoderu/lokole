FROM mcr.microsoft.com/azure-cli:2.66.0

# Install only missing packages to avoid breaking Azure CLI's curl/libssh2 linkage
# The azure-cli image already has curl, jq, ca-certificates, wget
RUN tdnf install -y \
        tar \
        util-linux \
        python3-pip

# Install Docker CLI from Docker's official repository for API 1.44+ support
# Use curl instead of wget since azure-cli already has curl
RUN curl -fsSL -o /tmp/docker.tgz "https://download.docker.com/linux/static/stable/x86_64/docker-27.4.1.tgz" && \
    tar -xzf /tmp/docker.tgz -C /tmp && \
    mv /tmp/docker/docker /usr/local/bin/ && \
    rm -rf /tmp/docker /tmp/docker.tgz && \
    chmod +x /usr/local/bin/docker

WORKDIR /app

COPY docker/integtest/requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY .env .
COPY docker/integtest/ ./

CMD ["./tests.sh"]
