COUNTS_PER_90_DEG = 330752
COUNTS_PER_REV = COUNTS_PER_90_DEG * 4
COUNTS_PER_HOUR = COUNTS_PER_REV / 12.0
ZERO_HOUR = 6


def normalize_hour(hour: int) -> int:
    hour = hour % 12
    return 12 if hour == 0 else hour


def hour_to_counts(hour: int) -> int:
    hour = normalize_hour(hour)
    steps = (hour - ZERO_HOUR) % 12
    return round(steps * COUNTS_PER_HOUR)


def nearest_equivalent_target(current_counts: int, target_counts: int) -> int:
    candidates = (
        target_counts - COUNTS_PER_REV,
        target_counts,
        target_counts + COUNTS_PER_REV,
    )
    return min(candidates, key=lambda target: abs(target - current_counts))
