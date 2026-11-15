
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text, Table, MetaData, Index
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from config.logging_config import setup_logger

logger = setup_logger()

# Each table's unique record identifier
PRIMARY_KEYS = {
    "users": "user_id",
    "orders": "order_id",
    "products": "product_id",
    "etl_summary": "table_name",
}


def get_engine(db_path="output/pipeline.db"):
    try:
        database_path = Path(db_path)
        database_path.parent.mkdir(parents=True, exist_ok=True)

        engine = create_engine(
            f"sqlite:///{database_path.as_posix()}"
        )

        logger.info("SQLite database engine created: %s", database_path)
        return engine

    except Exception:
        logger.exception("Failed to create database engine.")
        raise


def load_table(df, table_name, engine):
    """Insert new records and update existing records using upsert."""

    try:
        if table_name not in PRIMARY_KEYS:
            raise ValueError(
                f"No unique identifier configured for '{table_name}'."
            )

        if df.empty:
            logger.warning("No records to load into '%s'.", table_name)
            return

        key_column = PRIMARY_KEYS[table_name]

        if key_column not in df.columns:
            raise ValueError(
                f"Required key '{key_column}' missing from '{table_name}'."
            )

        if df[key_column].isna().any():
            raise ValueError(
                f"Null values found in key '{key_column}'."
            )

        if df[key_column].duplicated().any():
            raise ValueError(
                f"Duplicate values found in key '{key_column}'."
            )

        logger.info(
            "Starting incremental load for '%s': %d records.",
            table_name,
            len(df)
        )

        with engine.begin() as connection:

            # Create the table on the first run if it doesn't exist.
            if not inspect(connection).has_table(table_name):
                df.head(0).to_sql(
                    name=table_name,
                    con=connection,
                    index=False,
                    if_exists="fail"
                )
                logger.info("Created new table '%s'.", table_name)

            # Reflect the existing database table.
            metadata = MetaData()
            table = Table(
                table_name,
                metadata,
                autoload_with=connection
            )

            if key_column not in table.c:
                raise ValueError(
                    f"Database table '{table_name}' has no "
                    f"'{key_column}' column."
                )

            # Create a unique index for SQLite upsert operations.
            index = Index(
                f"uq_{table_name}_{key_column}",
                table.c[key_column],
                unique=True
            )
            index.create(connection, checkfirst=True)

            # Convert missing values to None and timestamps to strings.
            clean_df = df.astype(object).where(pd.notna(df), None)

            records = clean_df.to_dict(orient="records")

            for record in records:
                for column, value in record.items():
                    if isinstance(value, pd.Timestamp):
                        record[column] = value.isoformat()
                    elif hasattr(value, "item"):
                        record[column] = value.item()

            # Build SQLite INSERT ... ON CONFLICT DO UPDATE.
            insert_statement = sqlite_insert(table).values(records)

            update_values = {
                column: insert_statement.excluded[column]
                for column in df.columns
                if column != key_column
            }

            if update_values:
                upsert_statement = insert_statement.on_conflict_do_update(
                    index_elements=[key_column],
                    set_=update_values
                )
            else:
                upsert_statement = insert_statement.on_conflict_do_nothing(
                    index_elements=[key_column]
                )

            connection.execute(upsert_statement)

        logger.info(
            "Incremental load completed for '%s': %d records processed.",
            table_name,
            len(df)
        )

    except Exception:
        logger.exception(
            "Incremental load failed for table '%s'.",
            table_name
        )
        raise


def verify_load(engine, table_name):
    try:
        inspector = inspect(engine)

        if not inspector.has_table(table_name):
            raise ValueError(
                f"Table '{table_name}' does not exist."
            )

        query = text(f'SELECT COUNT(*) FROM "{table_name}"')

        with engine.connect() as connection:
            count = connection.execute(query).scalar_one()

        logger.info(
            "Verified table '%s': %d rows.",
            table_name,
            count
        )

        return count

    except Exception:
        logger.exception(
            "Database verification failed for '%s'.",
            table_name
        )
        raise
