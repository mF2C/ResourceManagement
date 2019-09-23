##Dockerfile for ARM
FROM python:3.7-alpine
RUN apk add openrc    bash
RUN apk add --virtual .build-deps \
    gcc \
    python3-dev \
    libffi-dev \
    build-base\
    git \
    autoconf \
    && pip install netifaces docker
RUN mkdir /var/app
WORKDIR /var/app
ADD *.py ./
ADD requirements.txt ./
RUN pip3 install requests \
    py-cpuinfo \
    psutil \
    flask \
    urllib3 \
    && pip3 install docker
RUN apk add hwloc hwloc-dev hwloc-tools --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing/
CMD [ "python", "-u","./main.py" ]
