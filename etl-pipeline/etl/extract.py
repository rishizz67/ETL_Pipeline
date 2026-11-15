
import json
import pandas as pd
import requests

from config.logging_config import setup_logger

logger = setup_logger()

PRODUCTS_API_URL = "https://dummyjson.com/products"


def extract_csv(filepath):
    """Extract user data from CSV."""

    logger.info("Reading CSV source: %s", filepath)

    try:
        df = pd.read_csv(filepath)

        logger.info(
            "CSV extraction successful: %d rows, %d columns.",
            len(df),
            len(df.columns)
        )

        return df

    except Exception:
        logger.exception("Failed to extract CSV: %s", filepath)
        raise


def extract_json(filepath):
    """Extract order data from JSON."""

    logger.info("Reading JSON source: %s", filepath)

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)

        df = pd.DataFrame(data)

        logger.info(
            "JSON extraction successful: %d rows.",
            len(df)
        )

        return df

    except Exception:
        logger.exception("Failed to extract JSON: %s", filepath)
        raise


def extract_api():
    """Extract real product data from DummyJSON REST API."""

    logger.info("Starting real Products API extraction.")

    try:
        response = requests.get(
            PRODUCTS_API_URL,
            params={"limit": 10},
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict) or "products" not in data:
            raise ValueError("Unexpected API response structure.")

        products = data["products"]

        if not isinstance(products, list) or not products:
            raise ValueError("API returned no valid products.")

        df = pd.DataFrame(products)

        required_columns = [
            "id",
            "title",
            "category",
            "price",
            "stock"
        ]

        missing_columns = [
            column for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing API fields: {missing_columns}"
            )

        # Standardize API fields to match our ETL database schema
        df = df.rename(columns={
            "id": "product_id",
            "title": "name"
        })

        df = df[
            ["product_id", "name", "category", "price", "stock"]
        ].copy()

        df["price"] = pd.to_numeric(
            df["price"], errors="raise"
        )

        df["stock"] = pd.to_numeric(
            df["stock"], errors="raise"
        )

        logger.info(
            "Real API extraction successful: %d products.",
            len(df)
        )

        return df

    except Exception:
        logger.exception("Products API extraction failed.")
        raise
