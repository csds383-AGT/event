from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit
from common import peers
from common.records import FestHubError


def to_cents(price):
    try:
        cents = Decimal(price) * 100
    except InvalidOperation:
        raise FestHubError(f"ticket price must be a decimal number like 25.50, got {price}")
    if not cents.is_finite() or cents != cents.to_integral_value():
        raise FestHubError(f"ticket price must be a decimal number with at most 2 decimal places, got {price}")
    return int(cents)


def is_url(value):
    try:
        parts = urlsplit(value)
    except ValueError:
        return False
    host = parts.hostname or ""
    has_spaces = any(character.isspace() for character in value)
    return parts.scheme in ("http", "https") and ("." in host or host == "localhost") and not has_spaces
