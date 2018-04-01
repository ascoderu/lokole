FROM nginx:stable

ARG CLIENT_VERSION=
ARG CLIENT_DOWNLOAD_FOLDER="opwen_email_client-${CLIENT_VERSION}"
ARG CLIENT_DOWNLOAD_ARCHIVE="${CLIENT_DOWNLOAD_FOLDER}.tar.gz"
ARG CLIENT_DOWNLOAD_URL="https://pypi.io/packages/source/o/opwen_email_client/${CLIENT_DOWNLOAD_ARCHIVE}"

ARG BUILD_DEPENDENCIES="curl"
RUN apt-get -qq update \
  && apt-get -qq install -y ${BUILD_DEPENDENCIES} \
  && while ! curl -fsLO ${CLIENT_DOWNLOAD_URL}; do sleep 20s; done \
  && tar xf ${CLIENT_DOWNLOAD_ARCHIVE} \
  && mv ${CLIENT_DOWNLOAD_FOLDER}/opwen_email_client/webapp/static /static \
  && rm -rf ${CLIENT_DOWNLOAD_FOLDER} ${CLIENT_DOWNLOAD_ARCHIVE} \
  && apt-get -qq remove -y ${BUILD_DEPENDENCIES} \
  && rm -rf /var/lib/apt/lists/*

ADD nginx.conf /etc/nginx/conf.d/frontend.conf

RUN rm /etc/nginx/conf.d/default.conf
