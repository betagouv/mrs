FROM node:10-alpine

ENV DJANGO_SETTINGS_MODULE=mrs.settings
ENV UWSGI_MODULE=mrs.wsgi:application

ENV NODE_ENV=production
ENV PLAYLABS_PLUGINS=postgres,uwsgi,django,sentry
ENV PYTHONIOENCODING=UTF-8 PYTHONUNBUFFERED=1
ENV STATIC_URL=/static/ STATIC_ROOT=/app/static
ENV UWSGI_SPOOLER_NAMES=mail,stat UWSGI_SPOOLER_MOUNT=/app/spooler
ENV VIRTUAL_PROTO=uwsgi
ENV LOG=/app/log
ENV VIRTUAL_PROTO=uwsgi
EXPOSE 6789

RUN apk update && apk --no-cache upgrade && apk --no-cache add ca-certificates gettext shadow python3 py3-psycopg2 uwsgi-python3 uwsgi-http uwsgi-spooler dumb-init bash git curl && pip3 install --upgrade pip
RUN mkdir -p /app && usermod -d /app -l app node && groupmod -n app node && chown -R app:app /app
RUN curl -sL https://sentry.io/get-cli/ | bash
WORKDIR /app

ARG GIT_COMMIT
ENV GIT_COMMIT=$GIT_COMMIT

COPY yarn.lock .babelrc package.json /app/
RUN cd /app && yarn install --cache-folder /dev/shm/yarn --frozen-lockfile
RUN mkdir -p src/mrs
COPY src/mrs/static /app/src/mrs/static
COPY webpack.config.js /app/
RUN yarn prepare

COPY requirements.txt /app/requirements.txt
RUN pip3 install --upgrade -r /app/requirements.txt

COPY setup.py /app/
COPY src /app/src
RUN pip3 install --editable /app

RUN mkdir -p ${LOG}
RUN mkdir -p ${STATIC_ROOT}
# Use DEBUG here to inhibate security checks in settings for this command
RUN DEBUG=1 mrs collectstatic --noinput --clear

# Let user write to log
RUN chown -R app. ${LOG}
USER app
ADD predeploy /app/predeploy
RUN mkdir -p ${UWSGI_SPOOLER_MOUNT}

EXPOSE 6789

CMD /usr/bin/dumb-init uwsgi \
  --spooler=${UWSGI_SPOOLER_MOUNT}/mail \
  --spooler=${UWSGI_SPOOLER_MOUNT}/stat \
  --spooler-processes 8 \
  --socket=0.0.0.0:6789 \
  --chdir=/app \
  --plugin=python3,http \
  --module=$UWSGI_MODULE \
  --http-keepalive \
  --harakiri=120 \
  --max-requests=100 \
  --master \
  --workers=24 \
  --processes=12 \
  --chmod=666 \
  --log-5xx \
  --vacuum \
  --enable-threads \
  --reload-os-env \
  --post-buffering=8192 \
  --ignore-sigpipe \
  --ignore-write-errors \
  --disable-write-exception \
  --static-map $STATIC_ROOT=$STATIC_URL \
  --static-expires = /* 7776000 \
  --offload-threads = %k
