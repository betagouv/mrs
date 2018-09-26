FROM node:10-alpine

# utf8
ENV PYTHONIOENCODING UTF-8
ENV NODE_ENV production
ENV STATIC_URL /static
ENV STATIC_ROOT /code/static
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE mrs.settings
ENV VIRTUAL_PROTO uwsgi
ENV NODE_ENV production
ENV PLAYLABS_PLUGINS postgres,uwsgi,django,sentry
ENV DOCKER_RUN uwsgi uwsgi/base.ini uwsgi/dev.ini
ENV DOCKER_RUN_SECURE uwsgi uwsgi/base.ini uwsgi/production.ini
ENV USER uwsgi
ENV UWSGI_STATIC_MAP $STATIC_ROOT=$STATIC_URL
ENV UWSGI_SPOOLER_NAMES mail,stat
ENV UWSGI_SPOOLER_MOUNT /spooler

RUN mkdir -p ${STATIC_ROOT}
RUN mkdir -p ${UWSGI_SPOOLER_MOUNT}/{$UWSGI_SPOOLER_NAMES}
RUN mkdir -p /code/log

RUN apk update && apk --no-cache upgrade && apk --no-cache add shadow python3 py3-psycopg2 uwsgi-python3 uwsgi-http uwsgi-spooler dumb-init bash git curl

RUN deluser node && usermod -U -s /bin/bash -d /code -u 1000 uwsgi && groupmod -g 1000 uwsgi
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

# Use DEBUG here to inhibate security checks in settings for this command
RUN DEBUG=1 mrs collectstatic --noinput --clear

EXPOSE 6789

ARG GIT_COMMIT
ENV GIT_COMMIT ${GIT_COMMIT}

CMD /usr/bin/dumb-init su $USER -c $DOCKER_RUN
