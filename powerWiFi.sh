#!/bin/bash

DOCKER_NAME_DISCOVERY="discovery"
IS_LEADER=False

#if ! [ $(id -u) = 0 ]; then
#    echo "You must be root to execute the code."
#    exit -1
#fi

if [ "$1" == "" ]; then
    echo "Usage: $0 wifi_iface_name"
    echo -e "Detected list of ifaces: \n$(/sbin/iw dev | awk '$1=="Interface"{print $2}')"
    exit 0
fi

WIFI_LIST=$(/sbin/iw dev | awk '$1=="Interface"{print $2}')
WIFI_DEV="$1"

for w in $WIFI_LIST; do
    if [ "$w" == "$WIFI_DEV" ]; then
        echo "$1 Network Interface is connected."
        yes=1
        break
    fi
done;

if [ "$yes" != "1" ]; then
    echo "Network Interface not found."
    exit 1
fi

PHY=$(cat /sys/class/net/"$WIFI_DEV"/phy80211/name)

echo "Searching $DOCKER_NAME_DISCOVERY container."

#Monitor whether the discovery container has been created
while true
do
  if [[ $(docker ps -f "name=$DOCKER_NAME_DISCOVERY" --format '{{.Names}}' | wc -l) -gt 0 ]]
  then
    container_name=$(docker ps -f "name=$DOCKER_NAME_DISCOVERY" --format '{{.Names}}')
    break
  fi
done

echo "Docker found."

pid=$(docker inspect -f '{{.State.Pid}}' $container_name)
# Assign phy wireless interface to the container
#mkdir -p /var/run/netns
#ln -s /proc/"$pid"/ns/net /var/run/netns/"$pid"
#/sbin/iw phy "$PHY" set netns "$pid"
#Bring the wireless interface up
#docker exec -d "$container_name" ip link set "$WIFI_DEV" name wlan0
#WIFI_DEV="wlan0"
ip addr flush dev "$WIFI_DEV"
docker exec -d "$container_name" ifconfig "$WIFI_DEV" up


if [[ "$IS_LEADER" == "True" ]]
  then
    #Define the characteristics of the network that will be used by the leader
    SUBNET="192.168.7"
    IP_AP="192.168.7.1"
    NETMASK="/24"
    ### Assign an IP to the wifi interface
    echo "Configuring interface with IP address"
#    ip netns exec "$pid" ip addr flush dev "$WIFI_DEV"
#    ip netns exec "$pid" ip link set "$WIFI_DEV" up
#    ip netns exec "$pid" ip addr add "$IP_AP$NETMASK" dev "$WIFI_DEV"

    ip addr flush dev "$WIFI_DEV"
    ip link set "$WIFI_DEV" up
    ip addr add "$IP_AP$NETMASK" dev "$WIFI_DEV"

    ### iptables rules for NAT
    echo "Adding natting rule to iptables (container)"
#    ip netns exec "$pid" iptables -t nat -A POSTROUTING -s $SUBNET.0$NETMASK ! -d $SUBNET.0$NETMASK -j MASQUERADE
    iptables -t nat -A POSTROUTING -s $SUBNET.0$NETMASK ! -d $SUBNET.0$NETMASK -j MASQUERADE

    ### Enable IP forwarding
    echo "Enabling IP forwarding (container)"
#    ip netns exec "$pid" echo 1 > /proc/sys/net/ipv4/ip_forward
    echo 1 > /proc/sys/net/ipv4/ip_forward
  fi