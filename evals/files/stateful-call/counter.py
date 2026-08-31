sequence = iter((4, 9))


def next_value() -> int:
    return next(sequence)


def pair() -> tuple[int, int]:
    return next_value(), next_value()
