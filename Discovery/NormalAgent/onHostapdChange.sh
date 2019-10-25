#!/bin/bash
if [[ $2 == "AP-STA-CONNECTED" ]]
then
  echo "$3 has joined"
fi

if [[ $2 == "AP-STA-DISCONNECTED" ]]
then
  echo "$3 has left"
fi 
