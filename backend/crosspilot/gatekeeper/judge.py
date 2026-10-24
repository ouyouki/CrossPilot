"""The Gatekeeper: input ``(action, facts, ruleset)``, output ``Verdict`` (04 §3).

This module is a pure function plus a table lookup. It imports no network client,
no LLM SDK and no ORM — INV-8 is enforced by a test that parses this package's
imports, so adding such a dependency here will fail CI rather than pass review.

Decision order is exactly 01 §6:

1. unregistered action      -> ACTION_FORBIDDEN (raised, no approval created)
2. ruleset unusable/stale   -> HOLD
3. any BLOCK rule matched   -> BLOCK
4. any required fact unknown-> HOLD
5. registry disposition AUTO/ HUMAN_INITIATED -> ALLOW (human click path)
6. otherwise                -> REQUIRE_HUMAN
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..core.decision import Decision, Disposition, Reason, Severity, Tri, Verdict
from ..core.errors import ToolGateError
from ..core.facts import Facts
from ..registry.actions import ActionSpec, spec_or_none
from .rules import Freshness, RuleSet


def required_facts(spec: ActionSpec) -> frozenset[str]:
    return frozenset(spec.required_facts)


def _hold(missing: tuple[str, ...], reasons: tuple[Reason, ...], ruleset_version: str) -> Verdict:
    return Verdict(
        decision=Decision.HOLD,
        reasons=reasons,
        missing_facts=missing,
        ruleset_version=ruleset_version,
    )


def judge(
    actor: Any,
    action_name: str,
    facts: Facts,
    ruleset: RuleSet | None,
    now: datetime,
) -> Verdict:
    """Return a verdict for *action_name*.

    ``actor`` is accepted for symmetry with the audit record; it never changes
    the outcome. Authorization is the Tool Gate's job (04 §3.2, INV-19) and
    keeping it out of here is what makes the verdict reproducible.
    """
    del actor  # identity is audited, never a decision input

    try:
        spec = spec_or_none(action_name)
        if spec is None:
            # INV-7: unregistered means "does not exist", and no approval may be
            # created for something that cannot be described.
            raise ToolGateError("ACTION_FORBIDDEN", f"unregistered action: {action_name}")

        ruleset_version = ruleset.version if ruleset is not None else ""

        # Step 2: the decision engine must be usable. Governance actions are
        # exempt on purpose (04 §2.1), otherwise a stale rule set could never be
        # renewed — the deadlock the design calls out.
        if spec.depends_on_ruleset:
            if ruleset is None:
                return _hold(
                    (),
                    (
                        Reason(
                            rule_id="ruleset_unavailable",
                            severity=Severity.BLOCK,
                            message="rule set is not available",
                        ),
                    ),
                    ruleset_version,
                )
            freshness = ruleset.freshness(now)
            if freshness is Freshness.STALE:
                hours = ruleset.stale_hours(now)
                return _hold(
                    (),
                    (
                        Reason(
                            rule_id="ruleset_stale",
                            severity=Severity.BLOCK,
                            message=(
                                f"rule set expired {hours} h ago; approving now would apply "
                                "rules that may already be void — renew it first (ACT-RULESET-RENEW)"
                            ),
                        ),
                    ),
                    ruleset_version,
                )
            if freshness is Freshness.NOT_INTEGRATED:
                return _hold(
                    (),
                    (
                        Reason(
                            rule_id="ruleset_not_integrated",
                            severity=Severity.BLOCK,
                            message="no published rule set version; rules cannot be evaluated",
                        ),
                    ),
                    ruleset_version,
                )

            outcomes = ruleset.evaluate(spec.name, facts)
        else:
            outcomes = ()

        # Step 3: deterministic blocking rules.
        blocks = tuple(
            Reason(
                rule_id=outcome.rule.rule_id,
                severity=Severity.BLOCK,
                message=outcome.rule.rewrite_hint or "blocked by rule",
                rule_version=outcome.rule.version,
                hit_text=outcome.rule.matched_snippet(facts),
            )
            for outcome in outcomes
            if outcome.tri is Tri.MATCH and outcome.rule.severity is Severity.BLOCK
        )
        if blocks:
            return Verdict(
                decision=Decision.BLOCK,
                reasons=blocks,
                ruleset_version=ruleset_version,
            )

        # Step 4: any unknown fact stops the action. UNKNOWN is worth HOLD only,
        # so every unknown rule contributes its dependency list.
        missing: set[str] = {name for name in spec.required_facts if not facts.is_known(name)}
        for outcome in outcomes:
            if outcome.tri is Tri.UNKNOWN:
                missing.update(
                    name for name in outcome.rule.requires_facts if not facts.is_known(name)
                )
        if missing:
            return _hold(
                tuple(sorted(missing)),
                (
                    Reason(
                        rule_id="missing_facts",
                        severity=Severity.BLOCK,
                        message="required facts are UNKNOWN; nothing is executed",
                        facts=tuple(sorted(missing)),
                    ),
                ),
                ruleset_version,
            )

        # A rule that could not run is UNKNOWN, even when it declares no facts
        # (a crashing matcher must not degrade into "not triggered", INV-9).
        unknown = tuple(outcome.rule.rule_id for outcome in outcomes if outcome.tri is Tri.UNKNOWN)
        if unknown:
            return _hold(
                (),
                (
                    Reason(
                        rule_id="rule_unknown",
                        severity=Severity.BLOCK,
                        message="rules could not be evaluated; nothing is executed",
                        facts=unknown,
                    ),
                ),
                ruleset_version,
            )

        warnings = tuple(
            Reason(
                rule_id=outcome.rule.rule_id,
                severity=Severity.WARN,
                message=outcome.rule.rewrite_hint or "warning",
                rule_version=outcome.rule.version,
                hit_text=outcome.rule.matched_snippet(facts),
            )
            for outcome in outcomes
            if outcome.tri is Tri.MATCH and outcome.rule.severity is Severity.WARN
        )

        # Step 5/6.
        if spec.disposition is Disposition.AUTO:
            return Verdict(
                decision=Decision.ALLOW_AUTO,
                reasons=warnings,
                ruleset_version=ruleset_version,
            )
        if spec.disposition is Disposition.HUMAN_INITIATED:
            # The click *is* the decision (04 §2.1); the Gate still ran the
            # blocking rules above, so a human cannot click past a BLOCK.
            return Verdict(
                decision=Decision.ALLOW_AUTO,
                reasons=warnings,
                ruleset_version=ruleset_version,
                human_initiated=True,
            )
        return Verdict(
            decision=Decision.REQUIRE_HUMAN,
            reasons=warnings,
            ruleset_version=ruleset_version,
        )
    except ToolGateError:
        raise
    except Exception as exc:  # INV-9: a broken judge is an unknown, never a pass
        return _hold(
            (),
            (
                Reason(
                    rule_id="judge_error",
                    severity=Severity.BLOCK,
                    message=f"decision engine failed: {exc!r}",
                ),
            ),
            "",
        )


__all__ = ["judge", "required_facts"]
