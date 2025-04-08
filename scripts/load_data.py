import pandas as pd
from sqlalchemy import create_engine
import os
from datetime import datetime


def convert_to_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date()
    except:
        return datetime.strptime(date_str, '%Y-%m-%d').date()


def load_csv_to_postgres():
    engine = create_engine('postgresql://analytics:analytics@analytics-db/analytics')

    # Загрузка exchange_rates
    if os.path.exists('/opt/airflow/data/exchange_rates.csv'):
        df = pd.read_csv('/opt/airflow/data/exchange_rates.csv')
        df['currency_date'] = df['currency_date'].apply(convert_to_date)
        df.to_sql('exchange_rates', engine, if_exists='replace', index=False)

    # Загрузка transactions
    if os.path.exists('/opt/airflow/data/transactions.csv'):
        df = pd.read_csv('/opt/airflow/data/transactions.csv')
        df.to_sql('transactions', engine, if_exists='replace', index=False)


if __name__ == '__main__':
    load_csv_to_postgres()