import pytest
from backend.engines.projection_engine import generate_projection_table


def test_projection_growth_accuracy():
    """Validate the dataframe output of the yearly projection logic."""
    df = generate_projection_table(0, 10000, 0.12, 1)

    assert len(df) == 1
    assert df.iloc[0]["invested"] == 120000
    assert df.iloc[0]["returns"] > 0

    # Approx check for standard SIP FV over 1y at 12% ~ 128093.28
    assert abs(df.iloc[0]["total_value"] - 128093.28) < 10.0
