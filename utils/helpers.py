def clamp_score(value):
    """Normalize score into 0-100 range."""
    try:
        score = float(value)
    except (ValueError, TypeError):
        return 0.0
    return max(0.0, min(100.0, round(score, 2)))
