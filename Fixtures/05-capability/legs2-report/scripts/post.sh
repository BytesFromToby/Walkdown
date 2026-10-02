#!/usr/bin/env bash
# WALKDOWN FIXTURE :: stage 5 capability :: inert; hosts are .invalid; nothing runs. Expected results in Fixtures/ANSWERS/.
payload="{\"text\": \"$1\"}"
curl -X POST -H 'Content-type: application/json' --data "$payload" "https://hooks.chat.invalid/services/T0000/B0000/fixture"
