"""Regression guard for DEF-9.

`alembic.ini` shipped without an ``[alembic]`` section header, so
``alembic_command.upgrade()`` raised ``configparser.MissingSectionHeaderError``
on every startup. ``main.py``'s ``lifespan()`` swallowed it as a WARNING, so the
``20260702_01_create_lead_table`` migration never ran and ``leads.lead`` never
existed — every leads endpoint 500'd for months. These tests fail fast if the
ini ever regresses to a state Alembic cannot parse.
"""
import configparser
from pathlib import Path

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def test_alembic_ini_exists():
    assert ALEMBIC_INI.is_file(), f"{ALEMBIC_INI} is missing"


def test_alembic_ini_is_parseable_with_alembic_section():
    parser = configparser.ConfigParser()
    # read() silently ignores unreadable files; assert it actually consumed ours.
    assert parser.read(ALEMBIC_INI) == [str(ALEMBIC_INI)]
    assert parser.has_section("alembic"), (
        "alembic.ini has no [alembic] section — Alembic will raise "
        "MissingSectionHeaderError on startup (DEF-9)"
    )
    assert parser.get("alembic", "script_location") == "migrations"
