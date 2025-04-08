#!/bin/bash
set -e

echo "Waiting for Airflow Scheduler to be ready..."
max_retries=30
retry_interval=5

for ((i=1; i<=max_retries; i++)); do
  if airflow db check >/dev/null 2>&1; then
    echo "Airflow DB is ready"
    if airflow jobs check --job-type SchedulerJob --hostname "$(hostname)" >/dev/null 2>&1; then
      echo "Airflow Scheduler is ready"
      exit 0
    fi
  fi
  echo "Attempt $i/$max_retries: Scheduler not ready, waiting $retry_interval seconds..."
  sleep $retry_interval
done

echo "Error: Airflow Scheduler did not become ready in time" >&2
exit 1