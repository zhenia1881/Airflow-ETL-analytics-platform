#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h postgres -U airflow; do
  sleep 1
done

echo "Waiting for Airflow DB to initialize..."
until airflow db check; do
  sleep 5
done

echo "Airflow DB is ready"