from decimal import Decimal
from typing import Any


def should_notify(event: dict, preferences: list[Any]) -> dict[str, bool]:
    results: dict[str, bool] = {}
    transaction_type = event.get("type")
    amount = Decimal(str(event.get("amount", 0)))

    for pref in preferences:
        if not pref.enabled:
            results[pref.channel.value] = False
            continue

        if transaction_type == "WITHDRAWAL":
            results[pref.channel.value] = True
        elif transaction_type == "SELL":
            results[pref.channel.value] = True
        elif transaction_type == "BUY":
            results[pref.channel.value] = amount >= pref.min_amount
        else:
            results[pref.channel.value] = False

    return results
