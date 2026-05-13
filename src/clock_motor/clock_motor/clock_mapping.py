COUNTS_PER_90_DEG = 330752
COUNTS_PER_REV = COUNTS_PER_90_DEG * 4
COUNTS_PER_HOUR = COUNTS_PER_REV / 12.0

# 中文：homing 后的逻辑 0 对应表盘 6 点。
# English: Logical zero after homing corresponds to clock 6.
ZERO_HOUR = 6


def normalize_hour(hour: int) -> int:
    """Normalize user input to 1..12. / 把输入统一成 1 到 12。"""
    hour = hour % 12
    return 12 if hour == 0 else hour


def hour_to_counts(hour: int) -> int:
    """Convert clock hour to clockwise counts from clock 6.

    中文：把几点钟转换成从 6 点顺时针出发的 counts。
    English: Convert an hour mark to clockwise counts measured from clock 6.
    """
    hour = normalize_hour(hour)
    steps = (hour - ZERO_HOUR) % 12
    return round(steps * COUNTS_PER_HOUR)


def nearest_equivalent_target(current_counts: int, target_counts: int) -> int:
    """Choose the nearest equivalent target among adjacent revolutions.

    中文：同一个钟点可以差一整圈；这里选择距离当前位置最近的那个。
    English: The same hour can be one revolution apart; choose the nearest one.
    """
    candidates = (
        target_counts - COUNTS_PER_REV,
        target_counts,
        target_counts + COUNTS_PER_REV,
    )
    return min(candidates, key=lambda target: abs(target - current_counts))
