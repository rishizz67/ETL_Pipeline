from sqlalchemy import create_engine, text
from rich.console import Console

console = Console()

def get_engine(db_path="output/pipeline.db"):
    """Create SQLite engine"""
    engine = create_engine(f"sqlite:///{db_path}")
    return engine

def load_table(df, table_name, engine):
    """Load a dataframe into a SQLite table"""
    console.log(f"[blue][LOAD][/blue] Writing {len(df)} rows → table: '{table_name}'")
    df.to_sql(name=table_name, con=engine, if_exists="replace", index=False)
    console.log(f"[green]✓ '{table_name}' loaded successfully[/green]")

def verify_load(engine, table_name):
    """Verify data was written correctly"""
    import pandas as pd
    df = pd.read_sql(f"SELECT COUNT(*) as count FROM {table_name}", engine)
    count = df['count'][0]
    console.log(f"[green]✓ Verified '{table_name}': {count} rows in database[/green]")
    return count
