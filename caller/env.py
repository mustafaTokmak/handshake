"""Configuration the caller shares with the repair lab.

repair_lab.cli loads the project .env through python-dotenv, so the lab
enforces CONTACT_CALLBACK_TOKEN from that file. The caller must read the same
file or it authenticates its relay with nothing and loses a finding to a 401
after the call has already happened. Stdlib only, to match the rest of caller/.

Precedence: the process environment first, then caller/.env, then the project
.env. A caller-local file can therefore point a rehearsal at a stub lab without
touching the shared configuration.
"""
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = (HERE / ".env", HERE.parent / ".env")
LINE = re.compile(r"""^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$""")

_values = None


def _parse(text):
    found = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = LINE.match(line)
        if not match:
            continue
        name, value = match.group(1), match.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        found[name] = value
    return found


def _files():
    """Parsed .env contents, cached. Earlier files win."""
    global _values
    if _values is None:
        merged = {}
        for path in FILES:
            try:
                text = path.read_text()
            except OSError:
                continue
            for name, value in _parse(text).items():
                merged.setdefault(name, value)
        _values = merged
    return _values


def reload():
    """Drop the cache so a value added mid-demo is picked up."""
    global _values
    _values = None
    return _files()


def get(name, default=""):
    value = os.environ.get(name, "").strip()
    if value:
        return value
    return _files().get(name, "").strip() or default


def first(names, default=""):
    """The first of several aliases that carries a value."""
    for name in names:
        value = get(name)
        if value:
            return value
    return default
