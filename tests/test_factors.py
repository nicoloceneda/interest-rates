import pandas as pd

from src.transforms.term_structure import extract_level_slope_curvature


def test_extract_level_slope_curvature_expected_values() -> None:
    data = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-01", "2026-01-01"],
            "maturity_years": [2.0, 5.0, 10.0],
            "value": [3.5, 4.0, 4.5],
        }
    )

    result = extract_level_slope_curvature(data)
    row = result.iloc[0]

    assert row["level"] == 4.5
    assert row["slope"] == 1.0
    assert row["curvature"] == 0.0
