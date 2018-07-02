Build a custom Docker image for your client and register the client:

```sh
docker build \
  --build-arg OPWEN_CLIENT_NAME=<some alphanumeric name> \
  --build-arg CLIENT_VERSION=<release from pypi> \
  --build-arg CLOUDFLARE_KEY=<cloudflare credential> \
  --build-arg CLOUDFLARE_USER=<cloudflare credential> \
  --build-arg CLOUDFLARE_ZONE=<cloudflare credential> \
  --build-arg SENDGRID_KEY=<sendgrid api key> \
  --build-arg OPWEN_REMOTE_ACCOUNT_KEY=<azure storage credential> \
  --build-arg OPWEN_REMOTE_ACCOUNT_NAME=<azure storage credential> \
  --build-arg REGISTRATION_SERVER_TABLES_ACCOUNT_KEY=<azure storage credential> \
  --build-arg REGISTRATION_SERVER_TABLES_ACCOUNT_NAME=<azure storage credential> \
  --tag my_lokole \
  docker/app
```

Run the client:

```sh
docker run \
  --volume <some path>:/state \
  --publish <a port>:80 \
  --env OPWEN_SYNC_SCHEDULE=<crontab schedule string> \
  my_lokole
```
