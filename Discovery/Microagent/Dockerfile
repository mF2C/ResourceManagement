FROM python:3.7-alpine
RUN apk add openrc	bash	wireless-tools	net-tools	iw	wpa_supplicant	vim
RUN apk add --virtual .build-deps \
    gcc \
    python3-dev \
    libffi-dev \
    build-base\
    && pip install netifaces docker requests
ADD *.py *.conf *.sh *.json /discovery/
WORKDIR /discovery
RUN chmod +x onWpaCliChange.sh
ENV interface=wlan1
CMD ["python3" , "start.py"]