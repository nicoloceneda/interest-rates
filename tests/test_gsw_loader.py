import pandas as pd

from src.data.gsw import normalize_gsw_long_form


def test_normalize_gsw_long_form_accepts_tenor_columns() -> None:
    data = pd.DataFrame(
        {
            "Date": ["2026-01-01", "2026-01-02"],
            "1y": [4.1, 4.2],
            "2y": [4.0, 4.1],
            "10y": [4.5, 4.6],
        }
    )

    result = normalize_gsw_long_form(data, source="GSW")
    assert set(result.columns) == {"date", "maturity_years", "tenor", "value", "source"}
    assert result["maturity_years"].min() == 1.0
    assert result["maturity_years"].max() == 10.0
