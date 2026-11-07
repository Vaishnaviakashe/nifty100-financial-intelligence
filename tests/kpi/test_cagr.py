from src.analytics.cagr import (
    calculate_cagr,
    eps_cagr,
    pat_cagr,
    revenue_cagr,
    turnaround_flag,
)


def test_cagr():
    result = calculate_cagr(100, 121, 2)
    assert round(result, 2) == 10.0


def test_cagr_invalid_years():
    assert calculate_cagr(100, 200, 0) is None


def test_cagr_negative_start():
    assert calculate_cagr(-100, 200, 5) is None


def test_revenue_cagr():
    assert round(revenue_cagr(100, 121, 2), 2) == 10.0


def test_pat_cagr():
    assert round(pat_cagr(100, 121, 2), 2) == 10.0


def test_eps_cagr():
    assert round(eps_cagr(100, 121, 2), 2) == 10.0


def test_turnaround():
    assert turnaround_flag(-100, 50) is True


def test_no_turnaround():
    assert turnaround_flag(100, 150) is False
