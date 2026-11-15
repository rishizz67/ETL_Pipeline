
import json
import pandas as pd

from etl.quality import generate_data_quality_report


def test_generate_data_quality_report(tmp_path):

    users_raw = pd.DataFrame({
        "user_id": [1, 2],
        "email": ["alice@test.com", "invalid-email"]
    })

    users_clean = pd.DataFrame({
        "user_id": [1, 2],
        "email": ["alice@test.com", "2@unknown.com"]
    })

    orders_raw = pd.DataFrame({
        "amount": [100, None]
    })

    orders_clean = pd.DataFrame({
        "is_orphan": [False, True]
    })

    products_df = pd.DataFrame({
        "product_id": ["P01"]
    })

    cleaning_report = {
        "nulls_fixed": 1,
        "dups_removed": 0,
        "invalid_fixed": 1
    }

    report = generate_data_quality_report(
        users_raw,
        users_clean,
        orders_raw,
        orders_clean,
        products_df,
        cleaning_report,
        output_dir=tmp_path
    )

    assert report["record_counts"]["users_raw"] == 2
    assert report["data_quality"]["invalid_emails"] == 1
    assert report["data_quality"]["orphan_orders"] == 1

    assert (tmp_path / "data_quality_report.json").exists()
    assert (tmp_path / "data_quality_report.csv").exists()

    with open(tmp_path / "data_quality_report.json", encoding="utf-8") as file:
        saved_report = json.load(file)

    assert saved_report["record_counts"]["products"] == 1
