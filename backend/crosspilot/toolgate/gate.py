"""Tool Gate — the single exit to the outside world (04 §1, §5.2, §6).

Every side effect goes through :meth:`ToolGate.call`, which performs, in order:

1. identity stamping and registry lookup   (unregistered -> ACTION_FORBIDDEN)
2. authorization of the *actor*            (INV-19)
3. a Gatekeeper verdict                    (BLOCK / HOLD / REQUIRE_HUMAN)
4. approval binding, then CAS consumption  (INV-1, INV-17)
5. execution, then audit                   (INV-11)

The audit row is written even when a call is refused, and the refusal does not
roll it back — a rejected attempt is exactly what an auditor wants to see.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol

from ..approvals.model import Approval
from ..approvals.repo import InMemoryApprovalRepo
from ..approvals.service import ApprovalsService
from ..audit.log import AuditDecision, AuditLog
from ..core.actors import AGENT, HUMAN, Actor
from ..core.decision import Decision, Disposition
from ..core.errors import ToolGateError
from ..core.facts import Facts
from ..gatekeeper.judge import judge
from ..gatekeeper.rules import RuleSet
from ..registry.actions import (
    AGENT_TOOL_WHITELIST,
    REGISTRY,
    TOOL_CATALOG,
    ActionSpec,
    ToolSpec,
)


class PreconditionGuard(Protocol):
    """Re-checks PC-* in the gate and voids the approval when one fails."""

    def check(self, approval: Approval, *, now) -> None: ...


@dataclass(frozen=True, slots=True)
class ToolCall:
    actor: Actor
    tool: str
    shop_id: str
    #: Must equal ``TOOL_CATALOG[tool].action`` when given; kept explicit so the
    #: caller cannot smuggle a different action through a permissive tool.
    action: str | None = None
    facts: Facts = field(default_factory=Facts)
    params: Mapping[str, Any] = field(default_factory=dict)
    approval_id: str | None = None
    subject_refs: tuple[str, ...] = ()
    payload_hash: str | None = None


class ToolGate:
    def __init__(
        self,
        *,
        repo: InMemoryApprovalRepo,
        approvals: ApprovalsService,
        audit: AuditLog,
        clock,
        ruleset_provider: Callable[[], RuleSet | None],
        precondition_guard: PreconditionGuard | None = None,
    ) -> None:
        self.repo = repo
        self.approvals = approvals
        self.audit = audit
        self.clock = clock
        self._ruleset_provider = ruleset_provider
        self._guard = precondition_guard

    # -- public entry point -------------------------------------------------
    def call(self, request: ToolCall, execute: Callable[[Approval | None], Any]) -> Any:
        now = self.clock.now()
        audited = False
        try:
            tool = self._resolve(request)
            spec = self._authorize(request, tool)
            if spec is None:
                # Not a registry action (approval.create / notify.send): still
                # authorization-gated and audited, but there is nothing to judge.
                self._audit(request, AuditDecision.ALLOWED, {"tool": tool.name, "gated": False})
                audited = True
                return execute(None)

            ruleset = self._ruleset_provider()
            verdict = judge(request.actor, spec.name, request.facts, ruleset, now)

            if verdict.decision is Decision.BLOCK:
                self._audit(
                    request,
                    AuditDecision.BLOCKED,
                    {
                        "tool": tool.name,
                        "rules": [r.rule_id for r in verdict.reasons],
                    },
                    verdict.ruleset_version,
                )
                audited = True
                raise ToolGateError(
                    "BLOCKED",
                    "blocked by compliance/business rules",
                    rule_ids=tuple(r.rule_id for r in verdict.reasons),
                )
            if verdict.decision is Decision.HOLD:
                self._audit(
                    request,
                    AuditDecision.HELD,
                    {
                        "tool": tool.name,
                        "missing_facts": list(verdict.missing_facts),
                        "rules": [r.rule_id for r in verdict.reasons],
                    },
                    verdict.ruleset_version,
                )
                audited = True
                # The reason matters more than the code: "the rule set expired
                # 30 h ago" tells the operator what to do next.
                detail = "; ".join(r.message for r in verdict.reasons if r.message) or (
                    "required facts are UNKNOWN; nothing is executed"
                )
                raise ToolGateError(
                    "HELD_UNKNOWN",
                    detail,
                    missing_facts=verdict.missing_facts,
                    next_action="fill the missing facts, then retry",
                )

            if verdict.decision is Decision.REQUIRE_HUMAN:
                approval = self._bind(request, spec, now)
                self._audit(
                    request,
                    AuditDecision.ALLOWED,
                    {"tool": tool.name, "approval_id": approval.id, "bound": True},
                    verdict.ruleset_version,
                )
                audited = True
                try:
                    result = execute(approval)
                except Exception as exc:
                    self.approvals.mark_exec_failed(
                        approval, now=self.clock.now(), detail=repr(exc)
                    )
                    self._audit(
                        request,
                        AuditDecision.DENIED,
                        {"tool": tool.name, "approval_id": approval.id, "phase": "execution", "error": repr(exc)},
                        verdict.ruleset_version,
                    )
                    raise
                self.approvals.mark_executed(approval, now=self.clock.now())
                return result

            # ALLOW_AUTO (or a human-initiated click): no approval object.
            self._audit(
                request,
                AuditDecision.ALLOWED,
                {"tool": tool.name, "human_initiated": verdict.human_initiated},
                verdict.ruleset_version,
            )
            audited = True
            return execute(None)
        except ToolGateError as exc:
            if not audited:
                self._audit_refusal(request, exc)
            raise

    # -- steps ---------------------------------------------------------------
    def _resolve(self, request: ToolCall) -> ToolSpec:
        tool = TOOL_CATALOG.get(request.tool)
        if tool is None:
            raise ToolGateError("ACTION_FORBIDDEN", f"unknown tool: {request.tool}")
        if request.action is not None and request.action != tool.action:
            raise ToolGateError(
                "ACTION_FORBIDDEN",
                f"tool {tool.name} is registered for {tool.action!r}, not {request.action!r}",
            )
        return tool

    def _authorize(self, request: ToolCall, tool: ToolSpec) -> ActionSpec | None:
        actor = request.actor
        spec = REGISTRY.get(tool.action) if tool.action else None
        if tool.action is not None and spec is None:  # pragma: no cover - registry drift
            raise ToolGateError("ACTION_FORBIDDEN", f"unregistered action: {tool.action}")

        if request.tool == "approval.decide":
            # C-1 / AC-06: deciding is not a tool. Grant delegation goes through
            # the grant engine, never through an agent call.
            raise ToolGateError(
                "ACTION_FORBIDDEN", "a decision is not a tool call; only a person decides"
            )

        if actor.kind == HUMAN:
            if spec is not None and spec.approver_role and actor.role != spec.approver_role:
                raise ToolGateError(
                    "ACTION_FORBIDDEN",
                    f"{spec.name} needs the {spec.approver_role} role, actor is {actor.role}",
                )
            return spec

        if actor.kind == AGENT:
            allowed = AGENT_TOOL_WHITELIST.get(actor.agent_name or "", frozenset())
            if tool.name not in allowed:
                raise ToolGateError(
                    "ACTION_FORBIDDEN",
                    f"{actor.agent_name} has no {tool.name} in its tool whitelist",
                )
            if tool.callers and actor.agent_name not in tool.callers:
                raise ToolGateError(
                    "ACTION_FORBIDDEN", f"{actor.agent_name} is not a caller of {tool.name}"
                )
            if spec is not None and spec.disposition is Disposition.HUMAN_INITIATED:
                # INV-19: an agent may never perform a human-initiated action.
                raise ToolGateError(
                    "ACTION_FORBIDDEN",
                    f"{spec.name} is HUMAN_INITIATED and cannot be called by an agent",
                )
            if (
                spec is not None
                and spec.disposition is Disposition.HUMAN_APPROVAL
                and not request.approval_id
            ):
                raise ToolGateError(
                    "NOT_APPROVED", f"{spec.name} requires an approval (INV-1)"
                )
            return spec

        # SYSTEM: the scheduler/worker may run automatic work and execute an
        # already-approved action, but never a human-initiated one.
        if spec is not None and spec.disposition is Disposition.HUMAN_INITIATED:
            raise ToolGateError(
                "ACTION_FORBIDDEN", f"{spec.name} is HUMAN_INITIATED and needs a person"
            )
        return spec

    def _bind(self, request: ToolCall, spec: ActionSpec, now) -> Approval:
        if not request.approval_id:
            raise ToolGateError(
                "NOT_APPROVED",
                f"{spec.name} is a red-light action and no approval was presented (INV-1)",
            )
        try:
            approval = self.repo.get(request.approval_id)
        except KeyError as exc:
            raise ToolGateError("NOT_APPROVED", str(exc)) from exc

        if approval.action_type != spec.name:
            raise ToolGateError(
                "APPROVAL_MISMATCH",
                f"approval is for {approval.action_type}, execution is for {spec.name}",
            )
        if approval.shop_id != request.shop_id:
            raise ToolGateError("APPROVAL_MISMATCH", "approval belongs to another shop")
        if tuple(sorted(approval.subject_refs)) != tuple(sorted(request.subject_refs)):
            raise ToolGateError(
                "APPROVAL_MISMATCH",
                "approval does not cover this subject (no query-style refs allowed)",
            )
        if not request.payload_hash or approval.payload_hash != request.payload_hash:
            raise ToolGateError(
                "APPROVAL_MISMATCH",
                "payload hash differs from the approved payload (INV-17)",
            )

        if self._guard is not None:
            # Last-moment re-check; may VOID and raise PRECONDITION_FAILED.
            self._guard.check(approval, now=now)

        try:
            return self.repo.try_begin_execution(approval.id, now=now)
        except ToolGateError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise ToolGateError("APPROVAL_ALREADY_CONSUMED", repr(exc)) from exc

    # -- audit helpers --------------------------------------------------------
    def _audit(
        self,
        request: ToolCall,
        decision: AuditDecision,
        details: Mapping[str, Any],
        ruleset_version: str = "",
    ) -> None:
        self.audit.append(
            ts=self.clock.now(),
            actor_type=request.actor.kind,
            actor_id=request.actor.id,
            action=request.action or request.tool,
            target=",".join(request.subject_refs) or request.shop_id,
            decision=decision,
            ruleset_version=ruleset_version,
            details={"tool": request.tool, **details},
        )

    def _audit_refusal(self, request: ToolCall, exc: ToolGateError) -> None:
        decision = {
            "BLOCKED": AuditDecision.BLOCKED,
            "HELD_UNKNOWN": AuditDecision.HELD,
        }.get(exc.code, AuditDecision.DENIED)
        self._audit(
            request,
            decision,
            {
                "code": exc.code,
                "detail": exc.detail,
                "missing_facts": list(exc.missing_facts),
                "rule_ids": list(exc.rule_ids),
            },
        )


__all__ = ["PreconditionGuard", "ToolCall", "ToolGate"]
