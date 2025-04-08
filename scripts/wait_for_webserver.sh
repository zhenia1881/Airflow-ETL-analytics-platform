#!/bin/bash
until curl --fail http://airflow-webserver:8080/health; do
  echo "Waiting for Airflow Webserver to be ready..."
  sleep 5
done