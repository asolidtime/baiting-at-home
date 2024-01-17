#!/bin/bash

while true; do
    python3 main.py
    SLEEP_TIME=$(( RANDOM % 900 + 120 ))
    echo "Sleeping for $SLEEP_TIME seconds..."
    sleep $SLEEP_TIME
done
