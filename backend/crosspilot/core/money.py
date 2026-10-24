"""Money, canonical JSON and payload hashing (04 §5.1, INV-16).

Two rules are structural here, not conventions:

* ``float`` never enters a payload or a canonical form — ``CanonicalisationError``
  is raised instead, so a stray float fails loudly at hash time.
* CNY x FX is rounded **per line item** to whole JPY before summing, because
  AC-41 requires Python and PostgreSQL to produce the same margin; rounding a
  total and rounding per item disagree.

The canonical form is RFC 8785 (JCS) restricted to what a listing payload may
contain: objects with string keys, arrays, strings, integers, booleans, null.
"""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from collections.abc import Iterable, Mapping
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

JPY = "JPY"

_FOUR_PLACES = Decimal("0.0001")


class CanonicalisationError(TypeError):
    """Raised when a value cannot be canonicalised without losing precision."""


def dec(value: Any) -> Decimal:
    """Convert to Decimal without going through binary float."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):  # bool is an int; reject it explicitly
        raise CanonicalisationError("boolean is not a money value")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        return Decimal(value)
    raise CanonicalisationError(f"unsupported money value: {type(value)!r}")


def jpy(value: Any) -> int:
    """Round a single line item to whole JPY, half-up (03 §3.1)."""
    return int(dec(value).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def sum_line_items(values: Iterable[Any]) -> int:
    """Round each item to JPY, then sum (never sum then round)."""
    return sum(jpy(v) for v in values)


def fx_convert(amount_cny: Any, rate: Any) -> int:
    """CNY amount x CNY->JPY rate, rounded once for this line item."""
    return jpy(dec(amount_cny) * dec(rate))


def q4(value: Any) -> Decimal:
    """Margin comparison precision is 4 decimal places (04 §5.1)."""
    return dec(value).quantize(_FOUR_PLACES, rounding=ROUND_HALF_UP)


def margin_equal(left: Any, right: Any) -> bool:
    return q4(left) == q4(right)


# ---------------------------------------------------------------------------
# Canonical JSON (JCS subset)
# ---------------------------------------------------------------------------


def _sort_key(key: str) -> bytes:
    # JCS orders object keys by UTF-16 code units. Keys are ASCII today, but
    # encoding removes the doubt instead of relying on that.
    return key.encode("utf-16-be")


def _escape(text: str) -> str:
    out: list[str] = ['"']
    for ch in text:
        code = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\b":
            out.append("\\b")
        elif ch == "\f":
            out.append("\\f")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif code < 0x20:
            out.append(f"\\u{code:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def canonical_json(value: Any) -> str:
    """Serialise a payload to its RFC 8785 form (no whitespace, sorted keys)."""
    return _write(value)


def _write(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        # NFC keeps 〜 / ～ style variance out of the hash (03 §5.3).
        return _escape(unicodedata.normalize("NFC", value))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        raise CanonicalisationError(
            "float is not allowed in a canonical payload (INV-16); use int or str"
        )
    if isinstance(value, Decimal):
        raise CanonicalisationError(
            "Decimal must be converted to an int/string money value before hashing"
        )
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_write(item) for item in value) + "]"
    if isinstance(value, Mapping):
        parts: list[str] = []
        for key in sorted(value, key=_sort_key):
            if not isinstance(key, str):
                raise CanonicalisationError(f"payload keys must be strings: {key!r}")
            parts.append(f"{_escape(unicodedata.normalize('NFC', key))}:{_write(value[key])}")
        return "{" + ",".join(parts) + "}"
    if isinstance(value, (set, frozenset)):
        raise CanonicalisationError("sets are unordered; use a sorted list in payloads")
    raise CanonicalisationError(f"unsupported payload type: {type(value)!r}")


def sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def payload_hash(payload: Mapping[str, Any]) -> str:
    """``sha256(JCS(payload))`` — the value a human approval pins (03 §6.1)."""
    return sha256_hex(canonical_json(payload))


def is_finite_number(value: Any) -> bool:
    """Guard used by the import layer before a value becomes money."""
    return isinstance(value, (int, Decimal)) or (
        isinstance(value, float) and math.isfinite(value)
    )


__all__ = [
    "JPY",
    "CanonicalisationError",
    "canonical_json",
    "dec",
    "fx_convert",
    "is_finite_number",
    "jpy",
    "margin_equal",
    "payload_hash",
    "q4",
    "sha256_hex",
    "sum_line_items",
]
