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

  location / {
    proxy_pass_header Server;
    proxy_set_header Host \$http_host;
    proxy_redirect off;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Scheme \$scheme;

    location /api/email/sendgrid {
      proxy_pass http://apiemailreceive;
    }

    location /api/email/upload {
      proxy_pass http://apiclientwrite;
    }

    location /api/email/download {
      proxy_pass http://apiclientread;
    }
  }
}
