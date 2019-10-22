FROM python:3.7-slim-buster
RUN echo "deb http://http.debian.net/debian/ buster main contrib non-free" >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y -m hostapd dnsmasq iptables iw curl vim wpasupplicant net-tools wireless-tools firmware-ralink python3-dev gcc isc-dhcp-client procps
RUN echo "DAEMON_CONF="/etc/hostapd/hostapd.conf"" >> /etc/default/hostapd
RUN pip3 install flask netifaces requests psutil
ADD *.py *.conf *.sh *.json /discovery/
WORKDIR /discovery
RUN chmod +x onHostapdChange.sh
RUN chmod +x onWpaCliChange.sh
CMD ["python3", "app.py"]
