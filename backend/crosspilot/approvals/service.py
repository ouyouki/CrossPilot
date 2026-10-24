"""Approval lifecycle service (04 §4, §5.4).

Only a human may decide, and only with the version and payload hash the human
actually looked at (INV-18). Grant delegation does not come through here — the
grant engine approves deterministically and records ``delegated_via_grant_id``
so the audit never shows a grant approval as a personal signature (04 §4.1).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from ..core.actors import Actor, HUMAN
from ..core.errors import ToolGateError
from ..registry.actions import spec_or_none
from .model import Approval
from .preconditions import CheckResult, failures
from .repo import InMemoryApprovalRepo
from .state_machine import ApprovalStatus


class ApprovalDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    RETURN = "RETURN"


#: Predefined return reasons (03 §5.5); free text is optional and additive.
RETURN_REASON_CODES: frozenset[str] = frozenset(
    {"WORDING", "IMAGE", "PRICE", "COMPLIANCE", "OTHER"}
)


def new_approval_id() -> str:
    return f"ap-{uuid.uuid4().hex}"


class ApprovalsService:
    def __init__(self, repo: InMemoryApprovalRepo, clock) -> None:
        self.repo = repo
        self.clock = clock
        # 06 §4: view records live outside the approval so the approval stays
        # immutable after PENDING.
        self._views: dict[str, set[str]] = {}

    # -- views ------------------------------------------------------------
    def record_view(self, approval_id: str, *, user_id: str, section: str, now: datetime | None = None) -> set[str]:
        self.repo.get(approval_id)
        sections = self._views.setdefault(approval_id, set())
        sections.add(section)
        return set(sections)

    def viewed_sections(self, approval_id: str) -> set[str]:
        return set(self._views.get(approval_id, set()))

    # -- creation ----------------------------------------------------------
    def create(self, approval: Approval) -> Approval:
        return self.repo.add(approval)

    def submit(self, approval_id: str, *, now: datetime | None = None) -> Approval:
        now = now or self.clock.now()
        approval = self.repo.get(approval_id)
        updated = approval.transition(ApprovalStatus.PENDING, now=now)
        return self.repo.save(updated)

    # -- decisions ---------------------------------------------------------
    def decide(
        self,
        approval_id: str,
        *,
        actor: Actor,
        if_match_version: int,
        payload_hash: str,
        decision: ApprovalDecision,
        now: datetime | None = None,
        note: str = "",
        return_reason_code: str | None = None,
        precondition_results: tuple[CheckResult, ...] | None = None,
    ) -> Approval:
        now = now or self.clock.now()

        # INV-4: no machine signature, ever. A grant is the only non-human path
        # and it does not call this method.
        if actor.kind != HUMAN:
            raise ToolGateError(
                "ACTION_FORBIDDEN",
                "only a natural person may decide an approval (RL-2, ADR-13)",
            )

        approval = self.repo.get(approval_id)
        spec = spec_or_none(approval.action_type)
        if spec is None:  # pragma: no cover - registry drift guard
            raise ToolGateError("ACTION_FORBIDDEN", f"unknown action: {approval.action_type}")
        if spec.approver_role and actor.role != spec.approver_role:
            raise ToolGateError(
                "ACTION_FORBIDDEN",
                f"{approval.action_type} needs the {spec.approver_role} role",
            )

        if approval.status is not ApprovalStatus.PENDING:
            raise ToolGateError(
                "NOT_APPROVED", f"approval is {approval.status.value}, not PENDING"
            )
        if approval.version != if_match_version:
            raise ToolGateError(
                "VERSION_CONFLICT",
                f"approval changed since it was opened (v{if_match_version} -> v{approval.version})",
            )
        if approval.payload_hash != payload_hash:
            raise ToolGateError(
                "VERSION_CONFLICT", "payload hash does not match the approval (INV-18)"
            )

        missing_sections = set(approval.required_viewed) - self.viewed_sections(approval_id)
        if missing_sections:
            raise ToolGateError(
                "EVIDENCE_NOT_VIEWED",
                "required evidence was not opened",
                missing_sections=sorted(missing_sections),
            )

        if precondition_results is not None:
            bad = failures(precondition_results)
            if bad:
                voided, successor = self.void_and_succeed(approval, bad, now=now)
                raise ToolGateError(
                    "PRECONDITION_FAILED",
                    "; ".join(f"{r.pc} ({r.was} -> {r.now})" for r in bad),
                    failed=[r.as_failure() for r in bad],
                    successor_id=successor.id,
                    voided_id=voided.id,
                )

        if decision is ApprovalDecision.APPROVE:
            updated = approval.transition(
                ApprovalStatus.APPROVED,
                now=now,
                approver_user_id=actor.id,
                approver_kind="human",
                decided_at=now,
                decision_note=note,
            )
        elif decision is ApprovalDecision.REJECT:
            updated = approval.transition(
                ApprovalStatus.REJECTED,
                now=now,
                approver_user_id=actor.id,
                approver_kind="human",
                decided_at=now,
                decision_note=note,
            )
        else:
            if return_reason_code not in RETURN_REASON_CODES:
                raise ToolGateError(
                    "ACTION_FORBIDDEN",
                    f"RETURN needs one of the predefined reasons: {sorted(RETURN_REASON_CODES)}",
                )
            updated = approval.transition(
                ApprovalStatus.RETURNED,
                now=now,
                approver_user_id=actor.id,
                approver_kind="human",
                decided_at=now,
                decision_note=(note or return_reason_code or "").strip(),
                void_reasons=(),
            )
        return self.repo.save(updated)

    # -- void / successor ---------------------------------------------------
    def void_and_succeed(
        self,
        approval: Approval,
        failed: tuple[CheckResult, ...],
        *,
        now: datetime | None = None,
        successor_id: str | None = None,
        payload_hash: str | None = None,
    ) -> tuple[Approval, Approval]:
        """VOID the approval and open a new PENDING one that explains the diff.

        04 §5.4: the object is re-judged first; this method is only called when
        the outcome is still REQUIRE_HUMAN, which is the caller's responsibility.
        """
        now = now or self.clock.now()
        reasons = tuple(r.as_failure() for r in failed)
        # Generate the successor id up front: the unique-open-approval index
        # forbids two open approvals on one subject, so the old one must be
        # voided and relinked in the same step rather than patched afterwards.
        sid = successor_id or new_approval_id()
        voided = approval.transition(
            ApprovalStatus.VOID,
            now=now,
            void_reasons=reasons,
            successor_id=sid,
        )
        voided = self.repo.save(voided)

        diff = [
            {
                "pc": r.pc,
                "was": r.was,
                "now": r.now,
                "detail": r.detail,
            }
            for r in failed
        ]
        changes = dict(approval.what_changes)
        changes["diff_vs_previous_approval"] = diff
        successor_content = {
            "title": approval.title,
            "what_changes": changes,
            "why": approval.why,
            "impact": approval.impact,
            "evidence": approval.evidence,
            "alternatives": approval.alternatives,
            "recommendation": approval.recommendation,
            "required_viewed": approval.required_viewed,
            "preconditions": approval.preconditions,
            "payload_id": approval.payload_id,
            "payload_hash": payload_hash if payload_hash is not None else approval.payload_hash,
            "fact_snapshot_id": approval.fact_snapshot_id,
            "created_by_agent_id": approval.created_by_agent_id,
        }
        successor = Approval.new(
            approval_id=sid,
            shop_id=approval.shop_id,
            action_type=approval.action_type,
            subject_refs=approval.subject_refs,
            now=now,
            **successor_content,
        )
        successor = successor.transition(ApprovalStatus.PENDING, now=now)
        successor = self.repo.add(successor)
        return voided, successor

    # -- convenience ---------------------------------------------------------
    def mark_executed(self, approval: Approval, *, now: datetime | None = None) -> Approval:
        now = now or self.clock.now()
        return self.repo.save(approval.transition(ApprovalStatus.EXECUTED, now=now))

    def mark_exec_failed(
        self, approval: Approval, *, now: datetime | None = None, detail: str = ""
    ) -> Approval:
        now = now or self.clock.now()
        return self.repo.save(
            approval.transition(ApprovalStatus.EXEC_FAILED, now=now, decision_note=detail)
        )

    def mark_outcome_unknown(self, approval: Approval, *, now: datetime | None = None) -> Approval:
        now = now or self.clock.now()
        return self.repo.save(approval.transition(ApprovalStatus.OUTCOME_UNKNOWN, now=now))


__all__ = [
    "ApprovalDecision",
    "ApprovalsService",
    "RETURN_REASON_CODES",
    "new_approval_id",
]
