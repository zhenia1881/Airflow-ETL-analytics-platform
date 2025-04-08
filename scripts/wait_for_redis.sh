#!/bin/bash
set -e

counter=0
max_attempts=30

until nc -zv redis 6379; do
  sleep 5
  counter=$((counter+1))

  if [ $counter -ge $max_attempts ]; then
    exit 1
  fi
done