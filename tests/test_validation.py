import pytest

from src.validation import validate_bond_data


def test_validation_passes_with_required_columns(sample_bond_data):
    validate_bond_data(sample_bond_data)


def test_validation_fails_when_required_column_missing(sample_bond_data):
    bad_df = sample_bond_data.drop(columns=["OAS"])

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_bond_data(bad_df)