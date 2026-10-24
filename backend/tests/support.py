"""Test fixtures for the deterministic core.

Deliberately stdlib-only (unittest): the sandbox may not reach PyPI, and the
engine has no runtime dependency, so tests must not introduce one either.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from crosspilot.approvals.model import Approval
from crosspilot.approvals.preconditions import FactSnapshot, failures, evaluate
from crosspilot.approvals.repo import InMemoryApprovalRepo
from crosspilot.approvals.service import ApprovalDecision, ApprovalsService
from crosspilot.audit.log import AuditLog
from crosspilot.core.actors import Actor
from crosspilot.core.clock import FixedClock
from crosspilot.core.errors import ToolGateError
from crosspilot.core.facts import Facts
from crosspilot.gatekeeper.rules import RuleSet
from crosspilot.registry.actions import CONSENT2_ACTION
from crosspilot.toolgate.gate import ToolCall, ToolGate

SHOP = "shop-1"
NOW = datetime(2026, 10, 24, 0, 0, tzinfo=timezone.utc)

OPERATOR = Actor.human("u-operator", "Operator")
OWNER = Actor.human("u-owner", "Owner")
OTHER_OPERATOR = Actor.human("u-operator-2", "Operator")
PILOT = Actor.agent("Pilot")
SCOUT = Actor.agent("Scout")
CHECKER = Actor.agent("Checker")
LISTER = Actor.agent("Lister")
WORKER = Actor.system("worker")

PAYLOAD_HASH = "a" * 64


def ruleset(*, version: str = "rs-1", valid_days: int = 30, rules=(), now: datetime = NOW) -> RuleSet:
    return RuleSet(
        version=version,
        published_at=now,
        valid_until=now + timedelta(days=valid_days),
        rules=rules,
    )


def consent2_approval(
    *,
    approval_id: str = "ap-1",
    subject: str = "cand-1",
    payload_hash: str = PAYLOAD_HASH,
    required_viewed: tuple[str, ...] = (),
    action: str = CONSENT2_ACTION,
) -> Approval:
    return Approval.new(
        approval_id=approval_id,
        shop_id=SHOP,
        action_type=action,
        subject_refs=(subject,),
        now=NOW,
        title=f"上架新商品 {subject}",
        payload_hash=payload_hash,
        required_viewed=required_viewed,
    )


def consent2_facts(**overrides) -> Facts:
    base = {
        "cost_snapshot": "cs-1",
        "fx_rate": Decimal("19.80"),
        "compliance_report": "cr-1",
        "license_evidence": "lic-1",
        "payload_hash": PAYLOAD_HASH,
    }
    base.update(overrides)
    return Facts(base)


@dataclass
class Harness:
    clock: FixedClock
    repo: InMemoryApprovalRepo
    service: ApprovalsService
    audit: AuditLog
    gate: ToolGate
    ruleset: RuleSet | None

    def approve(self, approval: Approval, *, actor: Actor = OPERATOR, payload_hash: str | None = None) -> Approval:
        """Drive DRAFT -> PENDING -> APPROVED through the public service."""
        submitted = self.service.submit(approval.id, now=self.clock.now())
        for section in submitted.required_viewed:
            self.service.record_view(submitted.id, user_id=actor.id, section=section)
        return self.service.decide(
            submitted.id,
            actor=actor,
            if_match_version=submitted.version,
            payload_hash=payload_hash if payload_hash is not None else submitted.payload_hash,
            decision=ApprovalDecision.APPROVE,
            now=self.clock.now(),
        )

    def with_guard(self, guard) -> "Harness":
        self.gate = ToolGate(
            repo=self.repo,
            approvals=self.service,
            audit=self.audit,
            clock=self.clock,
            ruleset_provider=lambda: self.ruleset,
            precondition_guard=guard,
        )
        return self


def harness(*, rules=(), valid_days: int = 30, ruleset_version: str = "rs-1", guard=None) -> Harness:
    clock = FixedClock(NOW)
    repo = InMemoryApprovalRepo()
    service = ApprovalsService(repo, clock)
    audit = AuditLog()
    rs = ruleset(version=ruleset_version, valid_days=valid_days, rules=rules)
    gate = ToolGate(
        repo=repo,
        approvals=service,
        audit=audit,
        clock=clock,
        ruleset_provider=lambda: rs,
        precondition_guard=guard,
    )
    return Harness(clock=clock, repo=repo, service=service, audit=audit, gate=gate, ruleset=rs)


class PayloadGuard:
    """A precondition guard that only checks PC-PAYLOAD (INV-3)."""

    def __init__(self, service: ApprovalsService, current: FactSnapshot) -> None:
        self.service = service
        self.current = current
        self.voided: Approval | None = None
        self.successor: Approval | None = None

    def check(self, approval: Approval, *, now) -> None:
        snapshot = FactSnapshot(payload_hash=approval.payload_hash)
        results = evaluate(snapshot, self.current, now, preconditions=("PC-PAYLOAD",))
        bad = failures(results)
        if not bad:
            return
        voided, successor = self.service.void_and_succeed(
            approval, bad, now=now, payload_hash=self.current.payload_hash
        )
        self.voided, self.successor = voided, successor
        raise ToolGateError(
            "PRECONDITION_FAILED",
            "payload changed after approval",
            successor_id=successor.id,
        )


def execution_call(
    *,
    actor: Actor = LISTER,
    approval_id: str | None = None,
    subject: str = "cand-1",
    payload_hash: str | None = PAYLOAD_HASH,
    facts: Facts | None = None,
    tool: str = "listing.build_checklist",
) -> ToolCall:
    return ToolCall(
        actor=actor,
        tool=tool,
        shop_id=SHOP,
        facts=facts if facts is not None else consent2_facts(payload_hash=payload_hash),
        approval_id=approval_id,
        subject_refs=(subject,),
        payload_hash=payload_hash,
    )
