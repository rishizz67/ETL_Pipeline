
import pandas as pd
from etl.transform import clean_users, clean_orders


def test_clean_users_removes_duplicates():
    data = pd.DataFrame({
        "user_id": [1, 1, 2],
        "email": ["a@test.com", "a@test.com", "b@test.com"],
        "name": ["Alice", "Alice", "Bob"],
        "age": [25, 25, 30],
        "city": ["Delhi", "Delhi", "Mumbai"],
        "status": ["active", "active", "inactive"]
    })

    cleaned, report = clean_users(data)

    assert len(cleaned) == 2
    assert report["dups_removed"] == 1


def test_clean_orders_fixes_missing_amount():
    data = pd.DataFrame({
        "user_id": [1, 2],
        "amount": [100, None]
    })

    cleaned = clean_orders(data, valid_user_ids={1, 2})

    assert cleaned["amount"].isna().sum() == 0
    assert cleaned.loc[1, "amount"] == 0.0
