from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
from sqlalchemy import create_engine
import os

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def convert_to_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date()
    except:
        return datetime.strptime(date_str, '%Y-%m-%d').date()


def extract_data_from_project(project_name, last_execution_date):
    """Извлекает данные из CSV файлов проекта"""
    project_path = f'/opt/airflow/data/{project_name}'

    try:
        # Чтение user_sessions
        sessions_df = pd.read_csv(f'{project_path}/user_sessions.csv')
        sessions_df['updated_at'] = pd.to_datetime(sessions_df['updated_at'])
        sessions_df = sessions_df[sessions_df['updated_at'] > last_execution_date]

        if sessions_df.empty:
            return pd.DataFrame()

        # Чтение events
        events_df = pd.read_csv(f'{project_path}/events.csv')
        events_df['created_at'] = pd.to_datetime(events_df['created_at'])

        # Подсчет событий для каждой сессии
        events_count = []
        for _, session in sessions_df.iterrows():
            count = events_df[
                (events_df['user_id'] == session['user_id']) &
                (events_df['created_at'] >= session['created_at']) &
                (events_df['created_at'] <= session['updated_at'])
                ].shape[0]
            events_count.append(count)

        sessions_df['events_count'] = events_count
        sessions_df['project_name'] = project_name

        return sessions_df

    except Exception as e:
        print(f"Error processing {project_name}: {str(e)}")
        return pd.DataFrame()


def convert_to_usd(amount, currency, tx_date, exchange_rates):
    """Конвертирует сумму в USD"""
    if currency == 'USD':
        return amount

    rate = exchange_rates[
        (exchange_rates['currency_from'] == currency) &
        (exchange_rates['currency_to'] == 'USD') &
        (exchange_rates['currency_date'] == tx_date)
        ]['exchange_rate']

    return amount * rate.values[0] if not rate.empty else 0


def enrich_data_with_transactions(sessions_df, last_execution_date):
    """Обогащает данные транзакциями"""
    engine = create_engine('postgresql://analytics:analytics@analytics-db/analytics')

    # Получаем курсы валют
    exchange_rates = pd.read_sql('SELECT * FROM exchange_rates', engine)
    exchange_rates['currency_date'] = exchange_rates['currency_date'].apply(convert_to_date)

    # Получаем транзакции
    transactions = pd.read_sql('SELECT * FROM transactions', engine)
    transactions['created_at'] = pd.to_datetime(transactions['created_at'])

    enriched_data = []

    for _, session in sessions_df.iterrows():
        session_date = session['updated_at'].date()

        # Фильтруем транзакции пользователя за день сессии
        user_tx = transactions[
            (transactions['user_id'] == session['user_id']) &
            (transactions['created_at'].dt.date == session_date) &
            (transactions['success'] == True)
            ].sort_values('created_at')

        # Конвертируем суммы в USD
        user_tx['amount_usd'] = user_tx.apply(
            lambda tx: convert_to_usd(
                tx['amount'],
                tx['currency'],
                tx['created_at'].date(),
                exchange_rates
            ), axis=1
        )

        # Рассчитываем метрики
        transactions_sum = user_tx['amount_usd'].sum()

        first_tx_time = None
        first_tx_amount = None

        if not user_tx.empty:
            first_tx = user_tx.iloc[0]
            first_tx_time = first_tx['created_at']
            first_tx_amount = first_tx['amount_usd']

        # Формируем результат
        enriched_session = {
            'session_id': session['id'],
            'project_name': session['project_name'],
            'user_id': session['user_id'],
            'page_name': session['page_name'],
            'is_active': session['active'],
            'session_start_time': session['created_at'],
            'session_end_time': session['updated_at'],
            'last_activity_time': session['last_activity_at'],
            'events_count': session['events_count'],
            'transactions_sum_usd': transactions_sum,
            'first_successful_transaction_time': first_tx_time,
            'first_successful_transaction_usd': first_tx_amount
        }

        enriched_data.append(enriched_session)

    return pd.DataFrame(enriched_data)


def load_data_to_analytics_db(enriched_df):
    """Загружает данные в аналитическую БД"""
    if enriched_df.empty:
        return

    engine = create_engine('postgresql://analytics:analytics@analytics-db/analytics')

    # Конвертация datetime полей
    datetime_cols = ['session_start_time', 'session_end_time', 'last_activity_time',
                     'first_successful_transaction_time']
    for col in datetime_cols:
        if col in enriched_df.columns:
            enriched_df[col] = pd.to_datetime(enriched_df[col])

    enriched_df.to_sql(
        'analytics_sessions',
        engine,
        if_exists='append',
        index=False,
        method='multi'
    )


def process_project_data(project_name, last_execution_date_str, **context):
    """Обрабатывает данные проекта"""
    last_execution_date = datetime.strptime(last_execution_date_str, '%Y-%m-%d %H:%M:%S')

    # Извлекаем данные
    sessions_df = extract_data_from_project(project_name, last_execution_date)

    if sessions_df.empty:
        print(f"No new sessions found for {project_name}")
        return

    # Обогащаем данные
    enriched_df = enrich_data_with_transactions(sessions_df, last_execution_date)

    # Загружаем данные
    load_data_to_analytics_db(enriched_df)
    print(f"Processed {len(enriched_df)} sessions from {project_name}")


def get_last_execution_date(**context):
    """Получает дату последнего выполнения"""
    dag_run = context['dag_run']
    last_run = dag_run.get_previous_dagrun()

    if last_run:
        return last_run.execution_date.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return '1970-01-01 00:00:00'


with DAG(
        'user_sessions_etl',
        default_args=default_args,
        description='ETL process for user sessions aggregation',
        schedule_interval='*/10 * * * *',
        catchup=False,
        max_active_runs=1
) as dag:
    get_last_execution_task = PythonOperator(
        task_id='get_last_execution_date',
        python_callable=get_last_execution_date,
        provide_context=True,
        pool = 'default_pool'
    )

    process_project_a = PythonOperator(
        task_id='process_project_a',
        python_callable=process_project_data,
        op_args=['project_a', "{{ task_instance.xcom_pull(task_ids='get_last_execution_date') }}"],
        provide_context=True,
        pool = 'default_pool'
    )

    process_project_b = PythonOperator(
        task_id='process_project_b',
        python_callable=process_project_data,
        op_args=['project_b', "{{ task_instance.xcom_pull(task_ids='get_last_execution_date') }}"],
        provide_context=True,
        pool = 'default_pool'
    )

    process_project_c = PythonOperator(
        task_id='process_project_c',
        python_callable=process_project_data,
        op_args=['project_c', "{{ task_instance.xcom_pull(task_ids='get_last_execution_date') }}"],
        provide_context=True,
        pool='default_pool'
    )

    get_last_execution_task >> [process_project_a, process_project_b, process_project_c]