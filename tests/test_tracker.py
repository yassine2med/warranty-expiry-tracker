from datetime import date

import pytest

from warrantytracker.cli import main
from warrantytracker.tracker import Warranty, add_months, classify, load_warranties, status


def test_add_months_simple():
    assert add_months(date(2026, 1, 15), 3) == date(2026, 4, 15)


def test_add_months_clamps_month_end():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)


def test_add_months_leap_day():
    assert add_months(date(2024, 2, 29), 12) == date(2025, 2, 28)


def test_add_months_year_rollover():
    assert add_months(date(2026, 11, 30), 3) == date(2027, 2, 28)


def test_end_is_day_before_anniversary():
    assert Warranty("a", "v", date(2025, 1, 1), 12).end == date(2025, 12, 31)


def test_status_buckets():
    w = Warranty("a", "v", date(2025, 1, 1), 12)  # ends 2025-12-31
    assert status(w, date(2026, 1, 1), 90) == "expired"
    assert status(w, date(2025, 11, 1), 90) == "expiring"
    assert status(w, date(2025, 6, 1), 90) == "active"


def test_last_day_still_covered():
    w = Warranty("a", "v", date(2025, 1, 1), 12)
    assert status(w, date(2025, 12, 31), 0) == "expiring"


def test_classify_sorted_by_end():
    items = [Warranty("late", "v", date(2025, 3, 1), 12), Warranty("early", "v", date(2025, 1, 1), 12)]
    groups = classify(items, date(2025, 12, 1), 365)
    assert [w.asset for w in groups["expiring"]] == ["early", "late"]


def test_load_sample():
    assert len(load_warranties("data/warranties.csv")) == 9


def test_bad_months(tmp_path):
    p = tmp_path / "w.csv"
    p.write_text("asset,vendor,start_date,months\nx,v,2025-01-01,0\n")
    with pytest.raises(ValueError):
        load_warranties(str(p))


def test_bad_date(tmp_path):
    p = tmp_path / "w.csv"
    p.write_text("asset,vendor,start_date,months\nx,v,01/02/2025,12\n")
    with pytest.raises(ValueError):
        load_warranties(str(p))


def test_cli_output_file(tmp_path, capsys):
    out = tmp_path / "o.csv"
    assert main(["data/warranties.csv", "--as-of", "2026-11-19", "--out", str(out)]) == 0
    text = out.read_text()
    assert "expired" in text and "EXPIRING" in capsys.readouterr().out


def test_cli_negative_within():
    assert main(["data/warranties.csv", "--within", "-5"]) == 1
