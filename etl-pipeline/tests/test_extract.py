import pandas as pd
import pytest
import requests
from unittest.mock import patch, Mock

from etl.extract import extract_api


@patch("etl.extract.requests.get")
def test_extract_api_success(mock_get):
    mock_response = Mock()

    mock_response.json.return_value = {
        "products": [
            {
                "id": 1,
                "title": "Test Product",
                "category": "beauty",
                "price": 19.99,
                "stock": 50
            }
        ]
    }

    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    df = extract_api()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["product_id"] == 1
    assert df.iloc[0]["name"] == "Test Product"
    assert df.iloc[0]["price"] == 19.99

    mock_get.assert_called_once()


@patch("etl.extract.requests.get")
def test_extract_api_http_error(mock_get):
    mock_response = Mock()

    mock_response.raise_for_status.side_effect = requests.HTTPError(
        "API server error"
    )

    mock_get.return_value = mock_response

    with pytest.raises(requests.HTTPError):
        extract_api()