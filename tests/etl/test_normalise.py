import pytest

from src.etl.normaliser import PARSE_ERROR, normalize_ticker, normalize_year


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Mar-23", "2023-03"),
        ("Mar 23", "2023-03"),
        ("March-2023", "2023-03"),
        ("2023", "2023-03"),
        ("FY23", "2023-03"),
        ("FY2023", "2023-03"),
        ("Dec-22", "2022-12"),
        ("Jun-23", "2023-06"),
        ("2023-03", "2023-03"),
        ("Mar-24", "2024-03"),
        ("March 2024", "2024-03"),
        ("Dec 2024", "2024-12"),
        ("Jun 2024", "2024-06"),
        ("FY24", "2024-03"),
        ("FY 24", "2024-03"),
        ("2020", "2020-03"),
        ("2019-03", "2019-03"),
        ("  Mar-23  ", "2023-03"),
        ("garbage", PARSE_ERROR),
        ("", PARSE_ERROR),
    ],
)
def test_normalize_year(raw, expected):
    assert normalize_year(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("TCS", "TCS"),
        ("tcs", "TCS"),
        (" TCS ", "TCS"),
        ("tCs", "TCS"),
        ("BAJAJ-AUTO", "BAJAJ-AUTO"),
        ("bajaj-auto", "BAJAJ-AUTO"),
        (" BAJAJ-AUTO ", "BAJAJ-AUTO"),
        ("M&M", "M&M"),
        ("m&m", "M&M"),
        (" M&M ", "M&M"),
        ("INFY", "INFY"),
        (" infy ", "INFY"),
        ("RELIANCE", "RELIANCE"),
        ("reliance", "RELIANCE"),
        ("  HDFCBANK  ", "HDFCBANK"),
    ],
)
def test_normalize_ticker(raw, expected):
    assert normalize_ticker(raw) == expected
