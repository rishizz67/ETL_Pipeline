import pandas as pd
import json
from rich.console import Console

console = Console()

def extract_csv(filepath):
    """Extract data from a CSV file"""
    console.log(f"[blue][EXTRACT][/blue] Reading CSV: {filepath}")
    df = pd.read_csv(filepath)
    console.log(f"[green]✓ CSV loaded — {len(df)} rows, {len(df.columns)} columns[/green]")
    return df

def extract_json(filepath):
    """Extract data from a JSON file"""
    console.log(f"[blue][EXTRACT][/blue] Reading JSON: {filepath}")
    with open(filepath, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    console.log(f"[green]✓ JSON loaded — {len(df)} rows[/green]")
    return df

def extract_api():
    """Simulate a REST API call for product data"""
    console.log("[blue][EXTRACT][/blue] Calling Products API...")

    mock_api_response = [
        {"product_id": f"P{i:02d}", "name": name, "category": cat, "price": price, "stock": stock}
        for i, (name, cat, price, stock) in enumerate([
            ("Laptop Stand",       "Electronics", 1299,  45),
            ("Mechanical Keyboard","Electronics", 3499,  80),
            ("27\" Monitor",       "Electronics", 18999, 20),
            ("Wireless Mouse",     "Electronics", 999,  150),
            ("USB-C Hub",          "Electronics", 2499,  60),
            ("Webcam HD",          "Electronics", 4999,  35),
            ("Desk Lamp",          "Accessories", 799,  200),
            ("Mousepad XL",        "Accessories", 499,  300),
            ("Cable Organizer",    "Accessories", 299,  400),
            ("Laptop Bag",         "Accessories", 1999,  90),
        ], 1)
    ]

    df = pd.DataFrame(mock_api_response)
    console.log(f"[green]✓ API response — {len(df)} products fetched[/green]")
    return df
