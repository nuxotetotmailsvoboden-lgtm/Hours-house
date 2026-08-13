from datetime import datetime
import re

def parse_datetime(text: str) -> datetime | None:
    pattern = r'^(\d{2})\.(\d{2})\.(\d{4}) (\d{2}):(\d{2})$'
    match = re.match(pattern, text.strip())
    if not match:
        return None
    day, month, year, hour, minute = map(int, match.groups())
    try:
        return datetime(year, month, day, hour, minute)
    except ValueError:
        return None
