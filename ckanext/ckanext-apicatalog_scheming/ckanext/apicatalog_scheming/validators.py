def lower_if_exists(s):
    return s.lower() if s else s


def upper_if_exists(s):
    return s.upper() if s else s

def increment_if_exists(data, context):
    if 'save' in context:
        return int(data) + 1 if data else 0
    return data

def resource_validator(data):
    print data
    return int(data) + 1 if data else 0