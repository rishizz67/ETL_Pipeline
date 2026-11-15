
import pandas as pd

from config.logging_config import setup_logger

logger = setup_logger()


def clean_users(df):
    """Clean and fix dirty user data."""

    logger.info("Starting user data quality checks.")

    try:
        df = df.copy()
        original_count = len(df)

        report = {
            "nulls_fixed": 0,
            "dups_removed": 0,
            "invalid_fixed": 0
        }

        # 1. Remove duplicates
        df = df.drop_duplicates(subset=["user_id", "email"])

        report["dups_removed"] = original_count - len(df)

        logger.info(
            "Duplicate user records removed: %d",
            report["dups_removed"]
        )

        # 2. Fix blank/null names
        blank_names = (
            df["name"].isna()
            | df["name"].astype("string").str.strip().eq("").fillna(False)
        )

        df.loc[blank_names, "name"] = "Unknown User"

        report["nulls_fixed"] += int(blank_names.sum())

        # 3. Strip whitespace from names
        df["name"] = df["name"].astype("string").str.strip()

        # 4. Fix invalid emails
        invalid_email = (
            df["email"].isna()
            | ~df["email"].astype("string").str.contains(
                r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                na=False
            )
        )

        df.loc[invalid_email, "email"] = (
            df.loc[invalid_email, "user_id"].astype(str).str.lower()
            + "@unknown.com"
        )

        report["invalid_fixed"] += int(invalid_email.sum())

        # 5. Fix null/invalid ages
        df["age"] = pd.to_numeric(
            df["age"],
            errors="coerce"
        ).astype("float64")

        bad_age = (
            df["age"].isna()
            | (df["age"] < 0)
            | (df["age"] > 120)
        )

        median_age = df.loc[~bad_age, "age"].median()

        if pd.isna(median_age):
            median_age = 25

        df.loc[bad_age, "age"] = round(median_age)

        df["age"] = df["age"].fillna(25).astype(int)

        report["nulls_fixed"] += int(bad_age.sum())

        # 6. Fix null cities
        null_city = df["city"].isna()

        df.loc[null_city, "city"] = "Unknown"

        report["nulls_fixed"] += int(null_city.sum())

        logger.info(
            "User cleaning completed. Records: %d | Report: %s",
            len(df),
            report
        )

        return df, report

    except Exception:
        logger.exception("User data cleaning failed.")
        raise


def clean_orders(df, valid_user_ids):
    """Clean order data and flag orphan records."""

    logger.info("Starting order data cleaning.")

    try:
        df = df.copy()

        # Fix null amounts
        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

        null_amounts = df["amount"].isna()

        df.loc[null_amounts, "amount"] = 0.0

        # Flag orphan orders
        df["is_orphan"] = ~df["user_id"].isin(valid_user_ids)

        orphans = int(df["is_orphan"].sum())

        logger.info(
            "Order cleaning completed. Rows: %d | "
            "Null amounts fixed: %d | Orphan orders: %d",
            len(df),
            int(null_amounts.sum()),
            orphans
        )

        return df

    except Exception:
        logger.exception("Order data cleaning failed.")
        raise


def transform_users(df):
    """Add derived columns to users."""

    logger.info("Starting user transformations.")

    try:
        df = df.copy()

        df["segment"] = pd.cut(
            df["age"],
            bins=[0, 24, 34, 120],
            labels=["Youth", "Adult", "Senior"]
        ).astype(str)

        df["email_domain"] = df["email"].str.split("@").str[1]

        df["is_premium"] = (
            (df["status"].str.lower() == "active")
            & (df["age"] > 25)
        )

        df["status"] = df["status"].str.upper()

        df["etl_loaded_at"] = (
            pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        logger.info(
            "User transformations completed. Rows: %d",
            len(df)
        )

        return df

    except Exception:
        logger.exception("User transformation failed.")
        raise


def transform_orders(df):
    """Add derived columns to orders."""

    logger.info("Starting order transformations.")

    try:
        df = df.copy()

        df["amount"] = df["amount"].round(2)

        order_dates = pd.to_datetime(
            df["order_date"],
            errors="coerce"
        )

        df["order_year"] = order_dates.dt.year
        df["order_month"] = order_dates.dt.month

        df["etl_loaded_at"] = (
            pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        invalid_dates = int(order_dates.isna().sum())

        logger.info(
            "Order transformations completed. Rows: %d | Invalid dates: %d",
            len(df),
            invalid_dates
        )

        return df

    except Exception:
        logger.exception("Order transformation failed.")
        raise


def build_summary(users_df, orders_df, products_df):
    """Build a pipeline summary/audit table."""

    logger.info("Building ETL summary table.")

    try:
        loaded_at = str(pd.Timestamp.now())

        summary = pd.DataFrame([
            {
                "table_name": "users",
                "row_count": len(users_df),
                "loaded_at": loaded_at
            },
            {
                "table_name": "orders",
                "row_count": len(orders_df),
                "loaded_at": loaded_at
            },
            {
                "table_name": "products",
                "row_count": len(products_df),
                "loaded_at": loaded_at
            }
        ])

        logger.info("ETL summary table created successfully.")

        return summary

    except Exception:
        logger.exception("Failed to build ETL summary.")
        raise
