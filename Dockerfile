FROM node:10-alpine

# utf8
ENV PYTHONIOENCODING UTF-8

ENV NODE_ENV production

RUN apk update && apk --no-cache upgrade && apk --no-cache add shadow python3 py3-psycopg2 uwsgi-python3 uwsgi-http uwsgi-spooler dumb-init bash git curl

ENV STATIC_URL /static
ENV STATIC_ROOT /code/static
RUN mkdir -p ${STATIC_ROOT}
RUN mkdir -p /spooler/{mail,stat}
RUN mkdir -p /code/log

RUN deluser node && usermod -U -d /code -u 1000 uwsgi && groupmod -g 1000 uwsgi
WORKDIR /code

COPY yarn.lock .babelrc package.json /code/
RUN yarn install --frozen-lockfile
ADD src/mrs/static /code/src/mrs/static
ADD webpack.config.js /code
RUN yarn prepare

RUN pip3 install --upgrade pip
ADD requirements.txt /code/requirements.txt
RUN pip3 install --upgrade -r /code/requirements.txt

ADD setup.py /code/
ADD src /code/src
RUN pip3 install --editable /code

ADD .git /code/.git

# Use DEBUG here to inhibate security checks in settings for this command
RUN DEBUG=1 mrs collectstatic --noinput --clear

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE mrs.settings
ENV VIRTUAL_PROTO uwsgi
ENV NODE_ENV production
ARG GIT_COMMIT
ENV GIT_COMMIT ${GIT_COMMIT}

EXPOSE 6789

CMD /usr/bin/dumb-init uwsgi \
  --spooler=/spooler/mail \
  --spooler=/spooler/stat \
  --spooler-processes 8 \
  --socket=0.0.0.0:6789 \
  --chdir=/code \
  --plugin=python3,http \
  --module=mrs.wsgi:application \
  --http-keepalive \
  --harakiri=120 \
  --uid=$(id -u uwsgi) \
  --gid=$(id -g uwsgi) \
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
  --static-map $STATIC_ROOT=$STATIC_URL
