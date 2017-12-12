FROM ubuntu:artful

RUN apt-get update -y && apt-get upgrade -y && apt-get install -y python3-pip python3-psycopg2 unzip uwsgi-plugin-python3 uwsgi wget cron dumb-init
RUN useradd -md /code uwsgi
ENV STATIC_ROOT /code/static
RUN mkdir -p ${STATIC_ROOT}
RUN pip3 install --upgrade pip
ADD requirements.txt /code/requirements.txt
RUN pip3 install --upgrade -r /code/requirements.txt

ADD setup.py /code/setup.py
ADD src /code/src
RUN chown -R uwsgi. /code
RUN pip3 install --editable /code

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE mrs.settings
ENV VIRTUAL_PROTO uwsgi

# Use DEBUG here to inhibate security checks in settings for this command
RUN DEBUG=1 django-admin collectstatic --noinput --clear

EXPOSE 6789

CMD /usr/bin/dumb-init uwsgi \
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
  --post-buffering=8192
