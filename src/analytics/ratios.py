"""Profitability ratio calculations for Sprint 2."""


def net_profit_margin(net_profit, sales):
    """Calculate Net Profit Margin."""
    if sales == 0:
        return None

    return (net_profit / sales) * 100


def operating_profit_margin(operating_profit, sales):
    """Calculate Operating Profit Margin."""
    if sales == 0:
        return None

    return (operating_profit / sales) * 100


def return_on_equity(net_profit, equity_capital, reserves):
    """Calculate Return on Equity."""
    total_equity = equity_capital + reserves

    if total_equity <= 0:
        return None

    return (net_profit / total_equity) * 100


def return_on_capital_employed(
    ebit,
    equity_capital,
    reserves,
    borrowings,
):
    """Calculate Return on Capital Employed."""
    capital_employed = equity_capital + reserves + borrowings

    if capital_employed == 0:
        return None

    return (ebit / capital_employed) * 100


def cross_check_opm(calculated_opm, source_opm, tolerance=0.1):
    """Compare calculated OPM against the source OPM."""
    if calculated_opm is None or source_opm is None:
        return True

    return abs(calculated_opm - source_opm) <= tolerance


def debt_to_equity(borrowings, equity_capital, reserves):
    """Calculate Debt-to-Equity ratio."""
    total_equity = equity_capital + reserves

    if total_equity <= 0:
        return None

    return borrowings / total_equity


def interest_coverage(operating_profit, other_income, interest):
    """Calculate Interest Coverage Ratio."""
    if interest == 0:
        return 999

    return (operating_profit + other_income) / interest


def asset_turnover(sales, total_assets):
    """Calculate Asset Turnover ratio."""
    if total_assets == 0:
        return None

    return sales / total_assets
