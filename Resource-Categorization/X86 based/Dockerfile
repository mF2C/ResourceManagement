FROM python:3
RUN mkdir /var/app
WORKDIR /var/app
ADD *.py ./
ADD requirements.txt ./
RUN apt-get update
RUN apt-get --no-install-recommends -y install hwloc
RUN bash -c "pip install -r requirements.txt"
RUN bash -c "pip install docker"
#RUN bash -c "docker run --rm --net host alpine ifconfig"
CMD [ "python", "-u","./main.py" ]

