"""Problem-shaped errors for the Tool Gate and REST layer (07 §1.1).

One exception type carries the wire ``code``; the HTTP status is derived from a
single table so that the API layer cannot drift from the contract.
"""

from __future__ import annotations

from typing import Any

#: 07 §1.1 — code to HTTP status. Anything not listed is a server-side fault.
_CODE_STATUS: dict[str, int] = {
    "BLOCKED": 422,
    "HELD_UNKNOWN": 409,
    "NOT_APPROVED": 403,
    "EVIDENCE_NOT_VIEWED": 409,
    "PRECONDITION_FAILED": 409,
    "NOT_GRANTABLE": 422,
    "GRANT_WIDEN_FORBIDDEN": 422,
    "ACTION_FORBIDDEN": 403,
    "BUDGET_EXCEEDED": 422,
    "READINESS_INCOMPLETE": 409,
    "VERSION_CONFLICT": 412,
    # Not in 07 §1.1 but required to describe the failure honestly; both are
    # consequences of INV-17 (single-owner, single-shot approval consumption).
    "APPROVAL_ALREADY_CONSUMED": 409,
    "APPROVAL_MISMATCH": 409,
}


class ToolGateError(Exception):
    """A refused or failed Tool Gate call.

    The Gate audits every instance before re-raising (INV-11), so callers may
    treat this as the single failure signal.
    """

    def __init__(
        self,
        code: str,
        detail: str = "",
        *,
        rule_ids: tuple[str, ...] = (),
        missing_facts: tuple[str, ...] = (),
        next_action: str = "",
        **extra: Any,
    ) -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail
        self.rule_ids = rule_ids
        self.missing_facts = missing_facts
        self.next_action = next_action
        self.extra = extra

    @property
    def http_status(self) -> int:
        return _CODE_STATUS.get(self.code, 500)

    def as_problem(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "type": "about:blank",
            "title": self.code,
            "status": self.http_status,
            "code": self.code,
            "detail": self.detail,
        }
        if self.rule_ids:
            body["rule_ids"] = list(self.rule_ids)
        if self.missing_facts:
            body["missing_facts"] = list(self.missing_facts)
        if self.next_action:
            body["next_action"] = self.next_action
        body.update(self.extra)
        return body


class IdentityError(ToolGateError):
    """Unknown actor kind / unknown agent: never a business decision."""
