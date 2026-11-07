"""Cash-flow KPI calculations for Sprint 2."""


def free_cash_flow(cfo, cfi):
    """Calculate Free Cash Flow."""
    return cfo + cfi


def capex_intensity(capex, sales):
    """Calculate CapEx Intensity as a percentage of sales."""
    if sales == 0:
        return None

    return (abs(capex) / sales) * 100


def fcf_conversion(fcf, net_profit):
    """Calculate FCF Conversion as a percentage."""
    if net_profit == 0:
        return None

    return (fcf / net_profit) * 100


def cfo_quality_score(cfo, net_profit):
    """Calculate CFO Quality Score."""
    if net_profit == 0:
        return None

    return cfo / net_profit


def capital_allocation_pattern(cfo, cfi, cff):
    """Classify capital allocation from cash-flow signs."""

    cfo_sign = 1 if cfo > 0 else -1 if cfo < 0 else 0
    cfi_sign = 1 if cfi > 0 else -1 if cfi < 0 else 0
    cff_sign = 1 if cff > 0 else -1 if cff < 0 else 0

    patterns = {
        (1, -1, -1): "Reinvest",
        (1, -1, 1): "Expansion",
        (1, 1, -1): "Return",
        (1, 1, 1): "Cash Accumulation",
        (-1, -1, 1): "Distress",
        (-1, 1, 1): "Distress",
        (-1, -1, -1): "Distress",
        (-1, 1, -1): "Distress",
    }

    return patterns.get(
        (cfo_sign, cfi_sign, cff_sign),
        "Neutral",
    )


def negative_fcf_streak(fcf_values, required_years=3):
    """Check whether FCF was negative for consecutive years."""
    streak = 0

    for value in fcf_values:
        if value < 0:
            streak += 1
            if streak >= required_years:
                return True
        else:
            streak = 0

    return False
