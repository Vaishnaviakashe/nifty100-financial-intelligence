"""CAGR calculations for Sprint 2."""


def calculate_cagr(start_value, end_value, years):
    """Calculate CAGR as a percentage."""
    if years <= 0:
        return None

    if start_value <= 0 or end_value <= 0:
        return None

    return ((end_value / start_value) ** (1 / years) - 1) * 100


def revenue_cagr(start_revenue, end_revenue, years):
    """Calculate Revenue CAGR."""
    return calculate_cagr(start_revenue, end_revenue, years)


def pat_cagr(start_pat, end_pat, years):
    """Calculate PAT CAGR."""
    return calculate_cagr(start_pat, end_pat, years)


def eps_cagr(start_eps, end_eps, years):
    """Calculate EPS CAGR."""
    return calculate_cagr(start_eps, end_eps, years)


def turnaround_flag(start_value, end_value):
    """Identify negative-to-positive turnaround."""
    return start_value < 0 and end_value > 0
