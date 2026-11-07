from src.analytics.cashflow_kpis import (
    capex_intensity,
    capital_allocation_pattern,
    cfo_quality_score,
    fcf_conversion,
    free_cash_flow,
    negative_fcf_streak,
)


def test_free_cash_flow():
    assert free_cash_flow(500, -200) == 300


def test_capex_intensity():
    assert capex_intensity(-100, 1000) == 10


def test_capex_intensity_zero_sales():
    assert capex_intensity(-100, 0) is None


def test_fcf_conversion():
    assert fcf_conversion(300, 200) == 150


def test_fcf_conversion_zero_profit():
    assert fcf_conversion(300, 0) is None


def test_cfo_quality_score():
    assert cfo_quality_score(300, 200) == 1.5


def test_cfo_quality_zero_profit():
    assert cfo_quality_score(300, 0) is None


def test_reinvest_pattern():
    assert capital_allocation_pattern(100, -50, -20) == "Reinvest"


def test_expansion_pattern():
    assert capital_allocation_pattern(100, -50, 20) == "Expansion"


def test_return_pattern():
    assert capital_allocation_pattern(100, 50, -20) == "Return"


def test_distress_pattern():
    assert capital_allocation_pattern(-100, -50, 20) == "Distress"


def test_negative_fcf_streak():
    assert negative_fcf_streak([-10, -20, -30]) is True


def test_no_negative_fcf_streak():
    assert negative_fcf_streak([-10, -20, 30, -40]) is False
