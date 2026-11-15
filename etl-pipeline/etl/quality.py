
import json
from pathlib import Path

import pandas as pd

from config.logging_config import setup_logger

logger = setup_logger()


def generate_data_quality_report(
    users_raw,
    users_clean,
    orders_raw,
    orders_clean,
    products_df,
    cleaning_report,
    output_dir="reports"
):
    """Generate JSON and CSV reports for ETL data quality."""

    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        invalid_emails = (
            users_raw["email"].isna()
            | ~users_raw["email"].astype("string").str.contains(
                r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                na=False
            )
        )

        invalid_amounts = pd.to_numeric(
            orders_raw["amount"], errors="coerce"
        ).isna()

        report = {
            "record_counts": {
                "users_raw": int(len(users_raw)),
                "users_clean": int(len(users_clean)),
                "orders_raw": int(len(orders_raw)),
                "orders_clean": int(len(orders_clean)),
                "products": int(len(products_df))
            },
            "data_quality": {
                "missing_user_values": int(users_raw.isna().sum().sum()),
                "duplicate_users": int(
                    users_raw.duplicated(
                        subset=["user_id", "email"]
                    ).sum()
                ),
                "invalid_emails": int(invalid_emails.sum()),
                "missing_or_invalid_order_amounts": int(
                    invalid_amounts.sum()
                ),
                "orphan_orders": int(orders_clean["is_orphan"].sum())
            },
            "cleaning_actions": {
                key: int(value)
                for key, value in cleaning_report.items()
            }
        }

        json_file = output_path / "data_quality_report.json"
        csv_file = output_path / "data_quality_report.csv"

        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(report, file, indent=4)

        rows = []
        for section, metrics in report.items():
            for metric, value in metrics.items():
                rows.append({
                    "category": section,
                    "metric": metric,
                    "value": value
                })

        pd.DataFrame(rows).to_csv(csv_file, index=False)

        logger.info("Data quality reports generated successfully.")
        logger.info("JSON report: %s", json_file)
        logger.info("CSV report: %s", csv_file)

        return report

    except Exception:
        logger.exception("Failed to generate data quality reports.")
        raise
