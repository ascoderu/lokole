server {
  listen 80;

  resolver {{DNS_RESOLVER}};

  client_max_body_size 50M;

  location = /favicon.ico {
    root /static;
  }

  location = /robots.txt {
    root /static;
  }

  location /api/email/sendgrid {
    proxy_pass http://{{HOSTNAME_EMAIL_RECEIVE}};
  }

  location /api/email/upload {
    proxy_pass http://{{HOSTNAME_CLIENT_WRITE}};
  }

  location /api/email/download {
    proxy_pass http://{{HOSTNAME_CLIENT_READ}};
  }

  location /api/email/register {
    auth_basic "Authorized requests only";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://{{HOSTNAME_CLIENT_REGISTER}};
  }
}
