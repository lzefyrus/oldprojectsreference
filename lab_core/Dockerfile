FROM python:latest
ENV PYTHONUNBUFFERED 1

ENV C_FORCE_ROOT true

ENV APP_USER sandrol
ENV APP_ROOT /src
RUN mkdir /src;
RUN groupadd -r ${APP_USER} \
    && useradd -r -m \
    --home-dir ${APP_ROOT} \
    -s /usr/sbin/nologin \
    -g ${APP_USER} ${APP_USER}

RUN chmod -R 777 /src

WORKDIR ${APP_ROOT}

RUN apt-get install binutils  gdal-bin

RUN mkdir /config
ADD requirements.txt /config/
RUN pip install -r /config/requirements.txt

USER ${APP_USER}
ADD . ${APP_ROOT}
