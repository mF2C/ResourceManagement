FROM debian:jessie
RUN echo "deb http://http.debian.net/debian/ jessie main contrib non-free" >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y -m python3 hostapd dnsmasq iptables iw curl vim python3-pip python3-prettytable wpasupplicant net-tools wireless-tools firmware-ralink
RUN echo "DAEMON_CONF="/etc/hostapd/hostapd.conf"" >> /etc/default/hostapd
RUN pip3 install flask netifaces
ADD *.py *.conf *.sh *.json /discovery/
WORKDIR /discovery
RUN chmod +x onHostapdChange.sh
RUN chmod +x onWpaCliChange.sh
CMD ["python3", "app.py"]
