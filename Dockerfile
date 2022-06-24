FROM python:3.8

RUN apt update
RUN apt install -y nginx gcc musl-dev libffi-dev curl git rustc openssl gettext-base
RUN pip3 install --upgrade pip
RUN pip3 install poetry certbot-nginx certbot-dns-google

ARG GCP_AUTH
ARG NOTIFICATION_EMAIL
ARG DOMAIN
ARG STAGING=--test-cert
ENV INSTALL_DIR=/opt/langar
ENV DOMAIN=${DOMAIN}

WORKDIR /tmp
RUN echo ${GCP_AUTH} > /tmp/auth.json && chmod 600 /tmp/auth.json && certbot certonly ${STAGING} --dns-google -d ${DOMAIN} -m ${NOTIFICATION_EMAIL} --agree-tos --dns-google-credentials=/tmp/auth.json && rm /tmp/auth.json
## It's possible to separate out the above from the below to not recreate the cert each time, but requires a secure container registry to store the output in
## In that scenario, you'd make the below `FROM` the output of above.

#setup nginx

COPY nginx-conf langar.conf.template
WORKDIR /etc/nginx/sites-available
RUN envsubst '${DOMAIN}' < /tmp/langar.conf.template > langar.conf
WORKDIR /etc/nginx/sites-enabled
RUN ln -s ../sites-available/langar.conf .
RUN rm default

RUN certbot install --nginx -d ${DOMAIN} --cert-name=${DOMAIN} --redirect

## setup app
WORKDIR ${INSTALL_DIR}
COPY . .
RUN poetry install
ENV PYTHONUNBUFFERED=1
CMD nginx && poetry run langar_db && poetry run gunicorn --enable-stdio-inheritance -w 2 langar.app:app