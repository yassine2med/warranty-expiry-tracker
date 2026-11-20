"""Warranty end dates and expiry buckets."""
from __future__ import annotations

import calendar
import csv
from dataclasses import dataclass
from datetime import date


@dataclass
class Warranty:
    asset: str
    vendor: str
    start: date
    months: int

    @property
    def end(self) -> date:
        """Last covered day: start plus months, minus one day."""
        return add_months(self.start, self.months).fromordinal(add_months(self.start, self.months).toordinal() - 1)


def add_months(d: date, months: int) -> date:
    """Add calendar months, clamping to the last day of a shorter month (Jan 31 + 1 = Feb 28)."""
    index = d.year * 12 + d.month - 1 + months
    year, month = divmod(index, 12)
    month += 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def load_warranties(path: str) -> list[Warranty]:
    """Read warranties from CSV (asset, vendor, start_date, months)."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = {"asset", "vendor", "start_date", "months"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: missing columns {sorted(missing)}")
        items = []
        for n, row in enumerate(reader, start=2):
            try:
                months = int(row["months"])
                start = date.fromisoformat(row["start_date"])
            except ValueError:
                raise ValueError(f"{path} line {n}: bad start_date or months") from None
            if months < 1:
                raise ValueError(f"{path} line {n}: months must be 1 or more")
            items.append(Warranty(row["asset"].strip(), row["vendor"].strip(), start, months))
        return items


def status(w: Warranty, as_of: date, within: int) -> str:
    """Return 'expired', 'expiring' (ends within the window) or 'active'."""
    days = (w.end - as_of).days
    if days < 0:
        return "expired"
    return "expiring" if days <= within else "active"


def classify(items: list[Warranty], as_of: date, within: int = 90) -> dict[str, list[Warranty]]:
    """Group warranties by status; each group sorted by end date."""
    groups: dict[str, list[Warranty]] = {"expired": [], "expiring": [], "active": []}
    for w in sorted(items, key=lambda x: (x.end, x.asset)):
        groups[status(w, as_of, within)].append(w)
    return groups
