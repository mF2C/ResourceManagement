#!/usr/bin/env bash

printf '\e[0;33m %-15s \e[0m Starting...\n' [PoliciesTests]

function log {
    text="$2"
    if [[ $1 == "OK" ]]
    then
        printf '\e[0;33m %-15s \e[32m SUCCESS:\e[0m %s \n' [PoliciesTests] "$text"
    elif [[ $1 == "IF" ]]
    then
        printf '\e[0;33m %-15s \e[34m INFO:\e[0m %s \n' [PoliciesTests] "$text"
    else
        printf '\e[0;33m %-15s \e[0;31m FAILED:\e[0m %s \n' [PoliciesTests] "$text"
    fi
}

BASE_API_URL=`echo ${BASE_API_URL:="https://localhost/rm"} | tr -d '"'`


#### Policies Tests ####
# 1. Policies API
( [[ $(curl -I "${BASE_API_URL}/components" -ksS | head -n1 | cut -d" " -f2) -eq 200 ]] > /dev/null 2>&1 && \
    log "OK" "Policies API working properly") || \
    log "NO" "Policies API not working properly"


# 2. Policies Health
RMINFO=$(curl -XGET "${BASE_API_URL}/components" -ksS 2>/dev/null )
STARTED=$(echo "${RMINFO}" | jq -r ".started" 2>/dev/null)
POLICIES=$(echo "${RMINFO}" | jq -r ".policies" 2>/dev/null)
RUNNING=$(echo "${RMINFO}" | jq -r ".running" 2>/dev/null)

( [[ ${STARTED} == "true" ]]  && \
    log "OK" "Policies Agent Start workflow successfully started.") || \
    log "NO" "Agent Start workflow not started."
( [[ ${RUNNING} == "true" ]]  && \
    log "OK" "Policies sub-modules are currently running.") || \
    log "NO" "Policies sub-modules are NOT running."
( [[ ${POLICIES} == "true" ]]  && \
    log "OK" "Area Resilience sub-module succesfully started.") || \
    log "NO" "Area Resilience sub-module not started."
