FROM microsoft/azure-cli:2.0.32

ARG HELM_VERSION="v2.9.1"
ARG KUBECTL_VERSION="v1.10.3"

RUN apk add -q --no-cache jq curl && \
  curl -sLfO "https://storage.googleapis.com/kubernetes-helm/helm-${HELM_VERSION}-linux-amd64.tar.gz" && \
  tar xf "helm-${HELM_VERSION}-linux-amd64.tar.gz" && \
  mv "linux-amd64/helm" /usr/local/bin/helm && \
  chmod +x /usr/local/bin/helm && \
  rm -rf "linux-amd64" "helm-${HELM_VERSION}-linux-amd64.tar.gz" && \
  az aks install-cli --client-version "${KUBECTL_VERSION}" && \
  mkdir /secrets

ADD helm /app/helm
ADD docker/setup/* /app/

WORKDIR /app

CMD ["/app/setup.sh"]
