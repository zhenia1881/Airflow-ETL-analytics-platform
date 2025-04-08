#!/bin/bash

# Функция для проверки готовности Airflow
wait_for_airflow_db() {
    echo "Ожидание готовности базы данных Airflow..."
    local max_retries=30
    local retry_interval=5

    for ((i=1; i<=max_retries; i++)); do
        if airflow db check >/dev/null 2>&1; then
            echo "База данных Airflow готова"
            return 0
        fi
        echo "Попытка $i из $max_retries: База данных не готова, ожидание $retry_interval сек..."
        sleep $retry_interval
    done

    echo "Ошибка: База данных Airflow не стала доступна за отведенное время" >&2
    return 1
}

# Функция для создания подключения
create_connection() {
    local conn_id=$1
    local conn_type=$2
    local host=$3
    local login=$4
    local password=$5
    local schema=$6
    local port=${7:-5432}

    echo "Создание подключения $conn_id..."
    if airflow connections get $conn_id >/dev/null 2>&1; then
        echo "Подключение $conn_id уже существует, обновление..."
        airflow connections delete $conn_id
    fi

    airflow connections add \
        --conn-type $conn_type \
        --conn-host $host \
        --conn-login $login \
        --conn-password $password \
        --conn-schema $schema \
        --conn-port $port \
        $conn_id

    if [ $? -eq 0 ]; then
        echo "Подключение $conn_id успешно создано"
    else
        echo "Ошибка при создании подключения $conn_id" >&2
        return 1
    fi
}

# Основной скрипт
set -e

# Ожидаем готовности Airflow
wait_for_airflow_db || exit 1

# Создаем подключения к базам данных проектов
create_connection "project_a_db" "postgres" "project_a_host" "airflow" "airflow" "project_a_db"
create_connection "project_b_db" "postgres" "project_b_host" "airflow" "airflow" "project_b_db"
create_connection "project_c_db" "postgres" "project_c_host" "airflow" "airflow" "project_c_db"

# Подключение к аналитической БД
create_connection "analytics_db" "postgres" "analytics-db" "analytics" "analytics" "analytics"

echo "Все подключения успешно настроены"