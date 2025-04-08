from sqlalchemy import create_engine, text

def init_db():
    engine = create_engine('postgresql://analytics:analytics@analytics-db/analytics')

    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS exchange_rates (
            currency_from VARCHAR(3) NOT NULL,
            currency_to VARCHAR(3) NOT NULL,
            exchange_rate NUMERIC(15, 6) NOT NULL,
            currency_date DATE NOT NULL,
            PRIMARY KEY (currency_from, currency_to, currency_date)
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS transactions (
            project TEXT NOT NULL,
            id BIGINT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            amount NUMERIC(15, 2) NOT NULL,
            currency VARCHAR(3) NOT NULL,
            success BOOLEAN NOT NULL
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS analytics_sessions (
            session_id VARCHAR(255) PRIMARY KEY,
            project_name VARCHAR(50) NOT NULL,
            user_id BIGINT NOT NULL,
            page_name VARCHAR(255) NOT NULL,
            is_active BOOLEAN NOT NULL,
            session_start_time TIMESTAMP NOT NULL,
            session_end_time TIMESTAMP NOT NULL,
            last_activity_time TIMESTAMP NOT NULL,
            events_count INTEGER NOT NULL,
            transactions_sum_usd NUMERIC(15, 2),
            first_successful_transaction_time TIMESTAMP,
            first_successful_transaction_usd NUMERIC(15, 2),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """))

        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_analytics_sessions_user_id 
        ON analytics_sessions(user_id);
        """))

        conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_analytics_sessions_session_end_time 
        ON analytics_sessions(session_end_time);
        """))

        conn.commit()


if __name__ == '__main__':
    init_db()