FROM ubuntu:artful

# utf8
ENV PYTHONIOENCODING UTF-8

RUN apt-get update -y && apt-get upgrade -y && apt-get install -y python3-pip python3-psycopg2 unzip uwsgi-plugin-python3 uwsgi wget curl cron dumb-init locales gettext
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -
RUN apt-get install -y nodejs
RUN npm install -g yarn

RUN useradd -md /code uwsgi
WORKDIR /code

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE mrs.settings
ENV VIRTUAL_PROTO uwsgi
ENV NODE_ENV=production
EXPOSE 6789

ENV STATIC_URL /static
ENV STATIC_ROOT /code/static
RUN mkdir -p ${STATIC_ROOT}
RUN mkdir -p /tmp/spool && chown uwsgi /tmp/spool

COPY yarn.lock .babelrc package.json /code/
RUN yarn install --frozen-lockfile
ADD src/mrs/static /code/src/mrs/static
ADD webpack.config.js /code
RUN yarn prepare

RUN pip3 install --upgrade pip
ADD requirements.txt /code/requirements.txt
RUN pip3 install --upgrade -r /code/requirements.txt

ADD setup.py /code/setup.py
ADD src /code/src
RUN pip3 install --editable /code

# Use DEBUG here to inhibate security checks in settings for this command
RUN DEBUG=1 django-admin collectstatic --noinput --clear

ARG GIT_COMMIT
ENV GIT_COMMIT ${GIT_COMMIT}

CMD /usr/bin/dumb-init uwsgi \
  --spooler=/spooler/mail \
  --spooler=/spooler/stat \
  --spooler-processes 1 \
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
