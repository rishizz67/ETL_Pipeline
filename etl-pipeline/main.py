
import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from config.logging_config import setup_logger
from etl.extract import extract_csv, extract_json, extract_api
from etl.transform import (
    clean_users,
    clean_orders,
    transform_users,
    transform_orders,
    build_summary
)
from etl.load import get_engine, load_table, verify_load
from etl.quality import generate_data_quality_report


console = Console()
logger = setup_logger()


def save_performance_report(metrics):
    """Save pipeline performance metrics as a JSON report."""

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / "pipeline_metrics.json"

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=4)

    logger.info("Performance report saved: %s", report_path)


def run_pipeline():
    pipeline_start = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()

    metrics = {
        "started_at": started_at,
        "status": "running",
        "phase_durations_seconds": {},
        "records_extracted": {},
        "records_loaded": {},
        "database_row_counts": {}
    }

    engine = None

    try:
        os.makedirs("output", exist_ok=True)

        logger.info("ETL pipeline execution started.")

        console.print(Panel.fit(
            "[bold blue]ETL PIPELINE STARTING[/bold blue]\n"
            "Sources: users.csv | orders.json | products API\n"
            "Target: output/pipeline.db (SQLite)",
            title="ETL Runner"
        ))

        # EXTRACT PHASE
        phase_start = time.perf_counter()

        logger.info("Starting extraction phase.")
        console.rule("[bold blue]EXTRACT PHASE[/bold blue]")

        users_raw = extract_csv("data/users.csv")
        orders_raw = extract_json("data/orders.json")
        products_df = extract_api()

        total_extracted = (
            len(users_raw) + len(orders_raw) + len(products_df)
        )

        metrics["records_extracted"] = {
            "users": len(users_raw),
            "orders": len(orders_raw),
            "products": len(products_df),
            "total": total_extracted
        }

        metrics["phase_durations_seconds"]["extraction"] = round(
            time.perf_counter() - phase_start, 4
        )

        logger.info(
            "Extraction completed. Total records: %d",
            total_extracted
        )

        # TRANSFORM PHASE
        phase_start = time.perf_counter()

        logger.info("Starting transformation phase.")
        console.rule("[bold yellow]TRANSFORM PHASE[/bold yellow]")

        users_clean, report = clean_users(users_raw)
        logger.info("User cleaning report: %s", report)

        orders_clean = clean_orders(
            orders_raw,
            valid_user_ids=set(users_clean["user_id"])
        )

        users_final = transform_users(users_clean)
        orders_final = transform_orders(orders_clean)

        summary_df = build_summary(
            users_final,
            orders_final,
            products_df
        )

        generate_data_quality_report(
            users_raw=users_raw,
            users_clean=users_clean,
            orders_raw=orders_raw,
            orders_clean=orders_clean,
            products_df=products_df,
            cleaning_report=report
        )

        metrics["phase_durations_seconds"]["transformation"] = round(
            time.perf_counter() - phase_start, 4
        )

        logger.info("Transformation phase completed.")

        # LOAD PHASE
        phase_start = time.perf_counter()

        logger.info("Starting database loading phase.")
        console.rule("[bold green]LOAD PHASE[/bold green]")

        engine = get_engine("output/pipeline.db")

        tables = {
            "users": users_final,
            "orders": orders_final,
            "products": products_df,
            "etl_summary": summary_df
        }

        for table_name, dataframe in tables.items():
            load_table(dataframe, table_name, engine)
            metrics["records_loaded"][table_name] = len(dataframe)

        metrics["phase_durations_seconds"]["loading"] = round(
            time.perf_counter() - phase_start, 4
        )

        logger.info("All database tables loaded.")

        # VERIFICATION PHASE
        phase_start = time.perf_counter()

        logger.info("Starting database verification.")
        console.rule("[bold green]VERIFICATION[/bold green]")

        for table_name in tables:
            row_count = verify_load(engine, table_name)

            metrics["database_row_counts"][table_name] = row_count

            logger.info(
                "Verified table '%s': %d rows.",
                table_name,
                row_count
            )

        metrics["phase_durations_seconds"]["verification"] = round(
            time.perf_counter() - phase_start, 4
        )

        engine.dispose()
        engine = None

        # FINAL METRICS
        metrics["status"] = "success"
        metrics["total_duration_seconds"] = round(
            time.perf_counter() - pipeline_start, 4
        )
        metrics["completed_at"] = datetime.now(timezone.utc).isoformat()

        save_performance_report(metrics)

        logger.info(
            "ETL pipeline completed successfully in %.4f seconds.",
            metrics["total_duration_seconds"]
        )

        console.print(Panel.fit(
            f"[bold green]PIPELINE COMPLETE[/bold green]\n\n"
            f"Duplicates removed : {report['dups_removed']}\n"
            f"Nulls fixed        : {report['nulls_fixed']}\n"
            f"Invalid fixed      : {report['invalid_fixed']}\n"
            f"Total duration     : {metrics['total_duration_seconds']} sec\n\n"
            f"Performance report : reports/pipeline_metrics.json\n"
            f"Database saved at  : output/pipeline.db",
            title="Pipeline Summary"
        ))

    except Exception:
        metrics["status"] = "failed"
        metrics["total_duration_seconds"] = round(
            time.perf_counter() - pipeline_start, 4
        )
        logger.exception("ETL pipeline execution failed.")

        try:
            save_performance_report(metrics)
        except Exception:
            logger.exception("Could not save failure performance report.")

        console.print(
            "[bold red]Pipeline failed. Check logs/pipeline.log[/bold red]"
        )
        raise

    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    run_pipeline()
