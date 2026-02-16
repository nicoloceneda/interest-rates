import pandas as pd

from src.transforms.regime import label_regimes


def test_label_regimes_assigns_known_states() -> None:
    data = pd.DataFrame(
        {
            "slope": [-0.5, 0.5, 0.0],
            "level": [5.0, 2.0, 3.0],
            "rolling_volatility": [1.5, 0.3, 0.8],
        }
    )

    labeled = label_regimes(
        data,
        slope_flat_band=0.1,
        level_low_quantile=0.2,
        level_high_quantile=0.8,
        volatility_high_quantile=0.7,
    )

    regimes = labeled["regime"].tolist()
    assert "risk_off" in regimes
    assert "reflation" in regimes
