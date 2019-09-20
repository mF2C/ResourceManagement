#!/bin/bash -e
# Credits: https://github.com/fgg89/docker-ap/blob/master/docker_ap

function cleanup {
    echo "WARN: Shutting down this mF2C agent..."
    docker-compose -p mf2c down -v || echo "ERR: failed to deprovision docker-compose"
    #rm .env || echo "ERR: .env not found"
    rm docker-compose.yml || echo "ERR: compose file not found"
    #rm -rf mF2C || echo "ERR: cloned mF2C repository not found"
    #rm *.cfg *.conf || echo "ERR: configuration files not found"
    echo "INFO: Shutdown finished"
    exit 1
}
trap cleanup ERR

PROJECT=mf2c

progress() {
    # $1 is the current percentage, from 0 to 100
    # $2 onwards, is the text to appear in front of the progress bar
    char=""
    for i in $(seq 1 $(($1/2)))
    do
        char=$char'#'
    done
    printf "\r\e[K|%-*s| %3d%% %s\n" "50" "$char" "$1" "${@:2}";
}

write_compose_file() {
    cat > docker-compose.yml <<EOF
version: '3'
services:
  discovery:
    build: ~/ResourceManagement/Discoverynew
    container_name: mf2c_discovery
    expose:
      - 46040
    cap_add:
      - NET_ADMIN
  policy-mock:
    build: ~/ResourceManagement/policy-mock
    container_name: mf2c_policy
    depends_on:
      - discovery
    environment:
      - isLeader=False
    tty: true

EOF
}

usage='Usage:
'$0' [OPTIONS]

OPTIONS:
\n --shutdown
\t Shutdown and delete the running mF2C deployment
\n --isLeader
\t Installs the mF2C system as a leader. This option is ignored when used together with --shutdown
'

IS_LEADER=False
while [ "$1" != "" ]; do
  case $1 in
    --shutdown )          DELETE_MODE=True;
    ;;
    --isLeader )          IS_LEADER=True;
    ;;
    -h )        echo -e "${usage}"
    exit 1
    ;;
    * )         echo -e "Invalid option $1 \n\n${usage}"
    exit 1
  esac
  shift
done

if [[ ! -z $DELETE_MODE ]]
then
    cleanup
fi

echo '''
==============================================================
|                                                            |
|                     88888888888  ad888888b,    ,ad8888ba,  |
|                     88          d8"     "88   d8"     `"8b |
|                     88                  a8P  d8            |
| 88,dPYba,,adPYba,   88aaaaa          ,d8P"   88            |
| 88P    "88"    "8a  88"""""        a8P"      88            |
| 88      88      88  88           a8P         Y8,           |
| 88      88      88  88          d8"           Y8a.    .a8P |
| 88      88      88  88          88888888888    `"Y8888Y"   |
|                                                            |
==============================================================

'''

progress "0" "Preparing to install mF2C"

unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    *)          machine="UNKNOWN:${unameOut}"
esac

progress "5" "Checking OS compatibility"

#Find inet name
if [[ "$machine" == "Mac" ]]
then
    WIFI_DEV=$(networksetup -listallhardwareports | grep -1 "Wi-Fi" | awk '$1=="Device:"{print $2}')
    IN_USE=$(route -n get default | awk '$1=="interface:"{print $2}')
    echo "ERR: compatibility for Mac is not fully supported yet. Exit..."
    read -p "Do you wish to continue? [y/n]" yn
    case $yn in
        [Yy]* ) break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
elif [[ "$machine" == "Linux" ]]
then
    WIFI_DEV=$(iw dev | awk '$1=="Interface"{print $2}')
    IN_USE=$(ip r | grep default | cut -d " " -f5)
    #find corresponding phy name
    PHY=$(cat /sys/class/net/"$WIFI_DEV"/phy80211/name)
else
    echo "ERR: the mF2C system is not compatible with your OS: $machine. Exit..."
    exit 1
fi

progress "10" "Cloning mF2C"

#git clone https://github.com/mF2C/mF2C.git

progress "15" "Checking networking conflicts"

# Check that the given interface is not used by the host as the default route
if [[ "$IN_USE" == "$WIFI_DEV" ]]
then
    echo -e "${BLUE}[INFO]${NC} The selected interface is configured as the default route, if you use it you will lose internet connectivity"
    while true;
    do
        read -p "Do you wish to continue? [y/n]" yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Please answer yes or no.";;
        esac
    done
fi

progress "25" "Setup environment"

# Write env file to be used by docker-compose


#echo "TOPOLOGY=$ALLOWED_BACKUPS" >> .env

progress "40" "Deploying docker-compose services"

write_compose_file

# Copy configuration files


#Deploy compose
docker-compose -p $PROJECT up --build -d 

progress "70" "Waiting for discovery to be up and running"

#Monitor whether the discovery container has been created
#DOCKER_NAME_DISCOVERY="${PROJECT}_discovery_1"
DOCKER_NAME_DISCOVERY="mf2c_discovery"
while true
do
  if [[ $(docker ps -f "name=$DOCKER_NAME_DISCOVERY" --format '{{.Names}}') == $DOCKER_NAME_DISCOVERY ]]
  then break
  fi
done

progress "80" "Binding wireless interface with discovery container"

#Bind inet to discovery

pid=$(docker inspect -f '{{.State.Pid}}' $DOCKER_NAME_DISCOVERY)

# Assign phy wireless interface to the container
if [[ "$machine" != "Mac" ]]
then
  mkdir -p /var/run/netns
  ln -s /proc/"$pid"/ns/net /var/run/netns/"$pid"
  iw phy "$PHY" set netns "$pid"
  #Bring the wireless interface up
  docker exec -d "$DOCKER_NAME_DISCOVERY" ifconfig "$WIFI_DEV" up

  if [[ "$IS_LEADER" == "True" ]]
  then
    #Define the characteristics of the network that will be used by the leader
    SUBNET="192.168.7"
    IP_AP="192.168.7.1"
    NETMASK="/24"
    ### Assign an IP to the wifi interface
    progress "85" "Configuring interface with IP address"
    ip netns exec "$pid" ip addr flush dev "$WIFI_DEV"
    ip netns exec "$pid" ip link set "$WIFI_DEV" up
    ip netns exec "$pid" ip addr add "$IP_AP$NETMASK" dev "$WIFI_DEV"

    ### iptables rules for NAT
    progress "90" "Adding natting rule to iptables (container)"
    ip netns exec "$pid" iptables -t nat -A POSTROUTING -s $SUBNET.0$NETMASK ! -d $SUBNET.0$NETMASK -j MASQUERADE
    
    ### Enable IP forwarding
    progress "95" "Enabling IP forwarding (container)"
    ip netns exec "$pid" echo 1 > /proc/sys/net/ipv4/ip_forward
  fi

fi

progress "100" "Installation complete!"
