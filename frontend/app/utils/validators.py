import re


def sanitize_input(data):
    """Sanitize user input to prevent injection attacks"""
    if isinstance(data, str):
        # Remove potentially dangerous characters
        data = re.sub(r'[<>&\"\']', '', data)
        # Limit length
        data = data[:500]
    return data