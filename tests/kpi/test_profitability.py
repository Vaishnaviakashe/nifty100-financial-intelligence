from src.analytics.ratios import (
    cross_check_opm,
    net_profit_margin,
    operating_profit_margin,
    return_on_capital_employed,
    return_on_equity,
)


def test_net_profit_margin():
    assert net_profit_margin(100, 500) == 20


def test_net_profit_margin_zero_sales():
    assert net_profit_margin(100, 0) is None


def test_operating_profit_margin():
    assert operating_profit_margin(150, 500) == 30


def test_operating_profit_margin_zero_sales():
    assert operating_profit_margin(150, 0) is None


def test_return_on_equity():
    assert return_on_equity(100, 300, 200) == 20


def test_return_on_equity_negative_equity():
    assert return_on_equity(100, -300, 100) is None


def test_return_on_capital_employed():
    assert (
        return_on_capital_employed(
            200,
            300,
            200,
            500,
        )
        == 20
    )


def test_cross_check_opm():
    assert cross_check_opm(20.0, 20.05)


def test_cross_check_opm_failure():
    assert not cross_check_opm(20.0, 21.0)
