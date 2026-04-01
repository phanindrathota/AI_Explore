import pandas as pd

from etl_sf.transformations.rules import TransformEngine


def test_transform_engine_required_and_casting():
    df = pd.DataFrame(
        {
            "CustomerID": ["C1", None],
            "Amount": ["10.5", "abc"],
        }
    )
    mappings = [
        {"source": "CustomerID", "target": "customer_id", "dtype": "str", "required": True},
        {"source": "Amount", "target": "amount", "dtype": "float"},
    ]

    valid, rejects = TransformEngine.apply(df, mappings)

    assert len(valid) == 1
    assert len(rejects) == 1
    assert rejects.iloc[0]["reason"] == "required field missing"
