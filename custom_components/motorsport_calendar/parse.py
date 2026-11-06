"""Turn API responses into calendar sessions (no Home Assistant dependency)."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from .const import (
    F1_SESSIONS,
    MOTOGP_DEFAULT_MINUTES,
    MOTOGP_SESSIONS,
    SERIES_F1,
    SERIES_MOTOGP,
)

_OFFSET_RE = re.compile(r"([+-]\d\d)(\d\d)$")


def parse_dt(value: str | None) -> datetime | None:
    """ISO 8601 -> UTC datetime. Accepts +0300, +03:00 and Z."""
    if not value:
        return None
    value = value.strip().replace("Z", "+00:00")
    value = _OFFSET_RE.sub(r"\1:\2", value)
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _title(name: str) -> str:
    small = {"of", "de", "del", "la", "le"}
    words = name.strip().lower().split()
    return " ".join(w if (i and w in small) else w.capitalize() for i, w in enumerate(words))


def _label(table: dict, key: str, fallback: str, fallback_type: str, lang: str) -> tuple[str, str]:
    entry = table.get(key)
    if not entry:
        return fallback, fallback_type
    fr, en, stype = entry
    return (fr if lang == "fr" else en), stype


def motogp_gp_name(event: dict[str, Any]) -> str:
    """'QATAR AIRWAYS GRAND PRIX OF QATAR ' -> 'Qatar'."""
    name = (event.get("name") or "").strip()
    m = re.search(r"GRAND PRIX OF (?:THE )?(.+)$", name, re.I)
    if m:
        return _title(m.group(1))
    country = event.get("country")
    country = country.get("name") if isinstance(country, dict) else None
    return _title(country or name or "MotoGP")


def parse_motogp(events: list[dict[str, Any]], lang: str = "en") -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ev in events or []:
        if (ev.get("kind") or "").upper() != "GP":
            continue
        gp = motogp_gp_name(ev)
        circuit = (ev.get("circuit") or {}).get("name") or ""
        for b in ev.get("broadcasts") or []:
            cat = (b.get("category") or {}).get("acronym")
            if cat != "MGP" or (b.get("type") or "").upper() != "SESSION":
                continue
            if (b.get("status") or "").upper() in ("CANCELLED", "CANCELED"):
                continue
            code = (b.get("shortname") or "").upper()
            label, stype = _label(MOTOGP_SESSIONS, code, b.get("name") or code, (b.get("kind") or "other").lower(), lang)
            start = parse_dt(b.get("date_start"))
            if not start:
                continue
            end = parse_dt(b.get("date_end"))
            if not end or end <= start:
                end = start + timedelta(minutes=MOTOGP_DEFAULT_MINUTES.get(stype, 30))
            out.append(
                {
                    "uid": f"motogp-{b.get('id') or (gp + code + start.isoformat())}",
                    "series": SERIES_MOTOGP,
                    "summary": f"🏍️ MotoGP {gp} – {label}",
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "location": circuit,
                    "description": f"Series: MotoGP\nGP: {gp}\nSession: {stype}",
                    "session_type": stype,
                }
            )
    return out


def f1_gp_name(meeting: dict[str, Any] | None, session: dict[str, Any]) -> str:
    name = (meeting or {}).get("meeting_name") or ""
    name = re.sub(r"\s*Grand Prix\s*$", "", name, flags=re.I).strip()
    return name or session.get("location") or session.get("country_name") or "F1"


def parse_f1(sessions: list[dict[str, Any]], meetings: list[dict[str, Any]], lang: str = "en") -> list[dict[str, Any]]:
    by_key = {m.get("meeting_key"): m for m in meetings or []}
    out: list[dict[str, Any]] = []
    for s in sessions or []:
        if s.get("is_cancelled"):
            continue
        start = parse_dt(s.get("date_start"))
        if not start:
            continue
        end = parse_dt(s.get("date_end"))
        if not end or end <= start:
            end = start + timedelta(hours=1)
        raw = s.get("session_name") or ""
        label, stype = _label(F1_SESSIONS, raw, raw, (s.get("session_type") or "other").lower(), lang)
        gp = f1_gp_name(by_key.get(s.get("meeting_key")), s)
        location = ", ".join(x for x in (s.get("circuit_short_name"), s.get("country_name")) if x)
        out.append(
            {
                "uid": f"f1-{s.get('session_key') or (gp + raw + start.isoformat())}",
                "series": SERIES_F1,
                "summary": f"🏎️ F1 {gp} – {label}",
                "start": start.isoformat(),
                "end": end.isoformat(),
                "location": location,
                "description": f"Series: F1\nGP: {gp}\nSession: {stype}",
                "session_type": stype,
            }
        )
    return out
