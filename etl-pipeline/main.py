import os
from rich.console import Console
from rich.panel import Panel

from etl.extract import extract_csv, extract_json, extract_api
from etl.transform import (
    clean_users, clean_orders,
    transform_users, transform_orders,
    build_summary
)
from etl.load import get_engine, load_table, verify_load

console = Console()

def run_pipeline():
    os.makedirs("output", exist_ok=True)

    console.print(Panel.fit(
        "[bold blue]ETL PIPELINE STARTING[/bold blue]\n"
        "Sources: users.csv | orders.json | products API\n"
        "Target:  output/pipeline.db (SQLite)",
        title="🚀 ETL Runner"
    ))

    # ── EXTRACT ─────────────────────────────────
    console.rule("[bold blue]EXTRACT PHASE[/bold blue]")
    users_raw   = extract_csv("data/users.csv")
    orders_raw  = extract_json("data/orders.json")
    products_df = extract_api()
    console.log(f"[green]✓ Total extracted: {len(users_raw) + len(orders_raw) + len(products_df)} rows[/green]")

    # ── TRANSFORM ────────────────────────────────
    console.rule("[bold yellow]TRANSFORM PHASE[/bold yellow]")
    users_clean, report = clean_users(users_raw)
    console.log(f"[dim]Cleaning report: {report}[/dim]")

    orders_clean  = clean_orders(orders_raw, valid_user_ids=set(users_clean["user_id"]))
    users_final   = transform_users(users_clean)
    orders_final  = transform_orders(orders_clean)
    summary_df    = build_summary(users_final, orders_final, products_df)

    # ── LOAD ─────────────────────────────────────
    console.rule("[bold green]LOAD PHASE[/bold green]")
    engine = get_engine("output/pipeline.db")

    load_table(users_final,  "users",       engine)
    load_table(orders_final, "orders",      engine)
    load_table(products_df,  "products",    engine)
    load_table(summary_df,   "etl_summary", engine)

    # ── VERIFY ───────────────────────────────────
    console.rule("[bold green]VERIFICATION[/bold green]")
    for tbl in ["users", "orders", "products", "etl_summary"]:
        verify_load(engine, tbl)

    console.print(Panel.fit(
        f"[bold green]✓ PIPELINE COMPLETE[/bold green]\n\n"
        f"Duplicates removed : {report['dups_removed']}\n"
        f"Nulls fixed        : {report['nulls_fixed']}\n"
        f"Invalid fixed      : {report['invalid_fixed']}\n\n"
        f"Database saved at  : output/pipeline.db\n"
        f"Open with SQLite Viewer in VS Code to explore!",
        title="📊 Summary"
    ))

if __name__ == "__main__":
    run_pipeline()
