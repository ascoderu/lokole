FROM microsoft/azure-cli:2.0.32

ARG HELM_VERSION="3.2.1"
ARG KUBECTL_VERSION="1.14.8"
ENV KUBERNETES_VERSION="1.14.8"
ENV CERT_MANAGER_VERSION="0.8.0"
ENV NGINX_INGRESS_VERSION="0.3.7"

RUN apk add -q --no-cache \
    jq=1.5-r2 \
    sshpass=1.05-r0 \
  && wget -q "https://get.helm.sh/helm-v${HELM_VERSION}-linux-amd64.tar.gz" \
  && tar xf "helm-v${HELM_VERSION}-linux-amd64.tar.gz" \
  && mv "linux-amd64/helm" /usr/local/bin/helm \
  && chmod +x /usr/local/bin/helm \
  && rm -rf "linux-amd64" "helm-v${HELM_VERSION}-linux-amd64.tar.gz" \
  && az aks install-cli --client-version "${KUBECTL_VERSION}" \
  && mkdir /secrets

COPY docker/setup/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY helm /app/helm
COPY docker/setup/* /app/

WORKDIR /app

CMD ["/app/setup.sh"]
