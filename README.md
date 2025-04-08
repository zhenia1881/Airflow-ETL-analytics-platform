# Airflow ETL Analytics Platform

![Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE?style=for-the-badge&logo=Apache%20Airflow&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)

Платформа для агрегации данных пользовательских сессий из множества проектов с загрузкой в аналитическую БД.

## 📌 Особенности

- **Автоматизированный ETL-процесс** (ежедневные запуски)
- **Поддержка множества проектов** (масштабируемая архитектура)
- **Инкрементальная загрузка** (только новые данные)
- **Готовые дашборды** в аналитической БД
- **Полная контейнеризация** (Docker)

## 🚀 Быстрый старт

### Предварительные требования
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ свободной памяти

### Установка
```bash
https://github.com/zhenia1881/Airflow-ETL-analytics-platform.git
```

### Запуск
1. Запустите сервисы
```bash
docker-compose up -d --build
```
2. Инициализируйте Airflow:
```bash
docker-compose exec airflow-webserver airflow db init
docker-compose exec airflow-webserver airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
```   
3. Откройте интерфейс:
```bash
http://localhost:8080
```

## 🔧 Технический стек

Orchestration: Apache Airflow 2.5+

Database: PostgreSQL 13

Broker: Redis 7

Processing: Python 3.9, Pandas, SQLAlchemy

Infrastructure: Docker, Docker Compose

## 📈 Мониторинг

Доступные метрики:

airflow_sessions_processed - количество обработанных сессий

airflow_processing_time - время выполнения задач

