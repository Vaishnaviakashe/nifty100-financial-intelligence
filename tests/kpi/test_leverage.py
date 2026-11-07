from src.analytics.ratios import (
    asset_turnover,
    debt_to_equity,
    interest_coverage,
)


def test_debt_to_equity():
    assert debt_to_equity(500, 300, 200) == 1


def test_debt_to_equity_zero_equity():
    assert debt_to_equity(500, -300, 100) is None


def test_debt_free_company():
    assert debt_to_equity(0, 300, 200) == 0


def test_interest_coverage():
    assert interest_coverage(200, 50, 50) == 5


def test_interest_coverage_zero_interest():
    assert interest_coverage(200, 50, 0) == 999


def test_asset_turnover():
    assert asset_turnover(1000, 500) == 2


def test_asset_turnover_zero_assets():
    assert asset_turnover(1000, 0) is None
