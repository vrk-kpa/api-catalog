def lower_if_exists(s):
    return s.lower() if s else s


def upper_if_exists(s):
    return s.upper() if s else s

def increment_if_exists(number):
    return int(number) + 1 if number else 0