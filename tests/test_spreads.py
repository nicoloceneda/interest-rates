import pandas as pd

from src.transforms.spreads import calculate_spreads


def test_calculate_spreads_basic_curve() -> None:
    data = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-01", "2026-01-01", "2026-01-02", "2026-01-02", "2026-01-02"],
            "maturity_years": [2.0, 10.0, 30.0, 2.0, 10.0, 30.0],
            "value": [4.0, 4.8, 5.1, 3.9, 4.2, 4.9],
        }
    )

    result = calculate_spreads(
        data,
        spread_definitions={"10Y-2Y": (10.0, 2.0), "30Y-10Y": (30.0, 10.0)},
        date_col="date",
        maturity_col="maturity_years",
        value_col="value",
    )

    ten_two = [round(float(value), 6) for value in result[result["spread"] == "10Y-2Y"]["value"]]
    thirty_ten = [round(float(value), 6) for value in result[result["spread"] == "30Y-10Y"]["value"]]

    assert ten_two == [0.8, 0.3]
    assert thirty_ten == [0.3, 0.7]
