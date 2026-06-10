import pandas as pd
from rich.console import Console

console = Console()

def clean_users(df):
    """Clean and fix dirty user data"""
    console.log("[yellow][CLEAN][/yellow] Starting data quality checks on users...")

    original_count = len(df)
    report = {"nulls_fixed": 0, "dups_removed": 0, "invalid_fixed": 0}

    # 1. Remove duplicates
    df = df.drop_duplicates(subset=["user_id", "email"])
    report["dups_removed"] = original_count - len(df)
    if report["dups_removed"] > 0:
        console.log(f"[yellow]⚠ Removed {report['dups_removed']} duplicate rows[/yellow]")

    # 2. Fix blank/null names
    blank_names = df["name"].isna() | (df["name"].str.strip() == "")
    df.loc[blank_names, "name"] = "Unknown User"
    report["nulls_fixed"] += int(blank_names.sum())
    if blank_names.sum() > 0:
        console.log(f"[yellow]⚠ Fixed {blank_names.sum()} blank names → 'Unknown User'[/yellow]")

    # 3. Strip whitespace from names
    df["name"] = df["name"].str.strip()

    # 4. Fix invalid emails
    invalid_email = df["email"].isna() | ~df["email"].str.contains(r'^[^@]+@[^@]+\.[^@]+', na=False)
    df.loc[invalid_email, "email"] = df.loc[invalid_email, "user_id"].str.lower() + "@unknown.com"
    report["invalid_fixed"] += int(invalid_email.sum())
    if invalid_email.sum() > 0:
        console.log(f"[yellow]⚠ Fixed {invalid_email.sum()} invalid emails[/yellow]")

    # 5. Fix null/invalid ages
    df["age"] = pd.to_numeric(df["age"], errors='coerce')
    bad_age = df["age"].isna() | (df["age"] < 0) | (df["age"] > 120)
    median_age = df["age"].median()
    df.loc[bad_age, "age"] = median_age
    df["age"] = df["age"].fillna(25).astype(int)
    report["nulls_fixed"] += int(bad_age.sum())

    # 6. Fix null cities
    null_city = df["city"].isna()
    df.loc[null_city, "city"] = "Unknown"
    report["nulls_fixed"] += int(null_city.sum())

    console.log(f"[green]✓ Cleaning done — {len(df)} clean rows remaining[/green]")
    return df, report

def clean_orders(df, valid_user_ids):
    """Clean order data"""
    console.log("[yellow][CLEAN][/yellow] Cleaning orders...")

    # Fix null amounts
    null_amounts = df["amount"].isna()
    df.loc[null_amounts, "amount"] = 0.0
    if null_amounts.sum() > 0:
        console.log(f"[yellow]⚠ Fixed {null_amounts.sum()} null amounts → 0.0[/yellow]")

    # Flag orphan orders
    df["is_orphan"] = ~df["user_id"].isin(valid_user_ids)
    orphans = df["is_orphan"].sum()
    if orphans > 0:
        console.log(f"[yellow]⚠ Flagged {orphans} orphan orders (unknown user_id)[/yellow]")

    console.log(f"[green]✓ Orders cleaned — {len(df)} rows[/green]")
    return df

def transform_users(df):
    """Add derived/transformed columns to users"""
    console.log("[blue][TRANSFORM][/blue] Applying business transformations...")

    df["segment"] = pd.cut(
        df["age"],
        bins=[0, 24, 34, 120],
        labels=["Youth", "Adult", "Senior"]
    ).astype(str)

    df["email_domain"] = df["email"].str.split("@").str[1]
    df["is_premium"] = (df["status"] == "active") & (df["age"] > 25)
    df["status"] = df["status"].str.upper()
    df["etl_loaded_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    console.log("[green]✓ Added: segment, email_domain, is_premium, status(normalized), etl_loaded_at[/green]")
    return df

def transform_orders(df):
    """Transform orders — add derived columns"""
    console.log("[blue][TRANSFORM][/blue] Transforming orders...")

    df["amount"] = df["amount"].round(2)
    df["order_year"] = pd.to_datetime(df["order_date"], errors='coerce').dt.year
    df["order_month"] = pd.to_datetime(df["order_date"], errors='coerce').dt.month
    df["etl_loaded_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    console.log("[green]✓ Added: order_year, order_month, etl_loaded_at[/green]")
    return df

def build_summary(users_df, orders_df, products_df):
    """Build a pipeline summary/audit table"""
    console.log("[blue][TRANSFORM][/blue] Building summary table...")

    summary = pd.DataFrame([
        {"table_name": "users",    "row_count": len(users_df),    "loaded_at": str(pd.Timestamp.now())},
        {"table_name": "orders",   "row_count": len(orders_df),   "loaded_at": str(pd.Timestamp.now())},
        {"table_name": "products", "row_count": len(products_df), "loaded_at": str(pd.Timestamp.now())},
    ])

    console.log("[green]✓ Summary table built[/green]")
    return summary
