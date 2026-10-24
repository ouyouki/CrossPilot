"""Action registry and tool catalog — the constant tables of 04 §2 and 05 §3.

Two structural guarantees live here:

* an action that is not in :data:`REGISTRY` cannot be called at all (INV-7);
* the actions that must never exist are *absent*, and tests enumerate
  :data:`FORBIDDEN_ACTION_NAMES` to prove it (INV-12, NV-2, NV-3).

The registry is intentionally a plain tuple of frozen records: it is meant to be
mirrored into the ``action_registry`` table by a migration and compared by CI
(06 §1), so nothing here may depend on runtime state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..core.decision import Disposition, Reversibility

# ---------------------------------------------------------------------------
# Evidence kinds (04 §4.2). Named so the generator and the UI can agree.
# ---------------------------------------------------------------------------

EVIDENCE_COST_BREAKDOWN = "cost_breakdown"
EVIDENCE_DEMAND_SIGNAL = "demand_signal"
EVIDENCE_G0_VERDICT = "g0_verdict"
EVIDENCE_DIRECTION_DIFF = "direction_diff"
EVIDENCE_SCORE_BREAKDOWN = "score_breakdown"

EVIDENCE_ASSET_COMPARE = "asset_side_by_side"
EVIDENCE_COMPLIANCE_REPORT = "compliance_report_g1_g4"
EVIDENCE_BACKTRANSLATION = "ja_zh_backtranslation"
EVIDENCE_PRICE_MARGIN = "price_margin_breakdown"
EVIDENCE_PAYLOAD_PREVIEW = "payload_preview"
EVIDENCE_WARN_LIST = "warn_list"

EVIDENCE_BUDGET_USAGE = "budget_usage"
EVIDENCE_DEGRADATION_PLAN = "degradation_plan"
EVIDENCE_RISK_STATEMENT = "risk_statement"
EVIDENCE_SOURCE_OF_VALUE = "source_of_value"
EVIDENCE_ALTERNATIVES = "alternatives"
EVIDENCE_LOOSEN_DIFF = "old_new_values"

# ---------------------------------------------------------------------------
# Action spec
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ActionSpec:
    name: str
    disposition: Disposition
    reversibility: Reversibility
    undo: str
    external_effect: bool = False
    grantable: bool = False
    approver_role: str | None = None
    evidence_kinds: tuple[str, ...] = ()
    preconditions: tuple[str, ...] = ()
    guardrails: tuple[str, ...] = ()
    #: Governance/config actions must still work when the rule set is stale,
    #: otherwise "renew the stale rule set" would itself be blocked (04 §2.1).
    depends_on_ruleset: bool = True
    required_facts: tuple[str, ...] = ()
    subject_type: str | None = None

    def __post_init__(self) -> None:
        if self.disposition is Disposition.NEVER:
            raise ValueError(
                f"{self.name}: NEVER actions must not be registered at all (04 §2.2)"
            )
        if not self.undo:
            raise ValueError(f"{self.name}: undo must be declared (04 §8)")


def _spec(
    name: str,
    disposition: Disposition,
    reversibility: Reversibility,
    undo: str,
    **kwargs: object,
) -> ActionSpec:
    return ActionSpec(
        name=name,
        disposition=disposition,
        reversibility=reversibility,
        undo=undo,
        **kwargs,  # type: ignore[arg-type]
    )


_ACTION_SPECS: tuple[ActionSpec, ...] = (
    # --- imports, scoring, collection (04 §2.1) -------------------------
    _spec(
        "ACT-IMPORT-DATA",
        Disposition.HUMAN_INITIATED,
        Reversibility.REVERSIBLE,
        "revert the import batch (import_batches.reverted_at)",
        approver_role="Operator",
        subject_type="import_batch",
    ),
    _spec(
        "ACT-SCORE",
        Disposition.AUTO,
        Reversibility.REVERSIBLE,
        "recompute scores",
        subject_type="candidate",
    ),
    _spec(
        "ACT-COST-CALC",
        Disposition.AUTO,
        Reversibility.REVERSIBLE,
        "recompute the cost snapshot",
        required_facts=("rate_card", "fx_rate", "tax_regime"),
        subject_type="candidate",
    ),
    _spec(
        "ACT-COLLECT-RECORD",
        Disposition.AUTO,
        Reversibility.REVERSIBLE,
        "delete the collection entry",
        subject_type="source_item",
    ),
    _spec(
        "ACT-GENERATE-TEXT",
        Disposition.AUTO,
        Reversibility.REVERSIBLE,
        "discard the generated version",
        guardrails=("generation_budget", "retry_cap"),
        required_facts=("license_evidence",),
        subject_type="asset_set",
    ),
    _spec(
        "ACT-GENERATE-IMAGE",
        Disposition.AUTO,
        Reversibility.REVERSIBLE,
        "discard the generated version",
        guardrails=("generation_budget", "retry_cap"),
        required_facts=("license_evidence",),
        subject_type="asset_set",
    ),
    _spec(
        "ACT-GENERATE-VIDEO",
        Disposition.AUTO,
        Reversibility.REVERSIBLE,
        "discard the generated version",
        guardrails=("generation_budget", "retry_cap"),
        required_facts=("license_evidence",),
        subject_type="asset_set",
    ),
    _spec(
        "ACT-COMPLIANCE-CHECK",
        Disposition.AUTO,
        Reversibility.REVERSIBLE,
        "re-run against the published rule set",
        subject_type="asset_set",
    ),
    _spec(
        "ACT-BUILD-CHECKLIST",
        Disposition.AUTO,
        Reversibility.REVERSIBLE,
        "regenerate the checklist (allowed only after consent 2)",
        preconditions=("PC-PAYLOAD",),
        subject_type="listing_payload",
    ),
    _spec(
        "ACT-READBACK-COMPARE",
        Disposition.AUTO,
        Reversibility.REVERSIBLE,
        "re-import the readback and compare again",
        subject_type="listing_job",
    ),
    # --- the two consent gates (04 §2.1) --------------------------------
    _spec(
        "ACT-SELECT",
        Disposition.HUMAN_APPROVAL,
        Reversibility.REVERSIBLE,
        "drop the candidate",
        grantable=True,
        approver_role="Operator",
        evidence_kinds=(
            EVIDENCE_COST_BREAKDOWN,
            EVIDENCE_DEMAND_SIGNAL,
            EVIDENCE_G0_VERDICT,
            EVIDENCE_DIRECTION_DIFF,
            EVIDENCE_SCORE_BREAKDOWN,
        ),
        preconditions=("PC-COST", "PC-FX-FRESH", "PC-G0", "PC-DIRECTION", "PC-RULES"),
        guardrails=("daily_selection_cap",),
        required_facts=("cost_snapshot", "fx_rate", "g0_verdict", "direction_version"),
        subject_type="candidate",
    ),
    # "同意 2" is this action. The documents also call it ACT-APPROVE-ASSETS;
    # the evidence list of 04 §4.2 is attached here (see APPROVE_ASSETS_ALIAS).
    _spec(
        "ACT-LIST-CREATE",
        Disposition.HUMAN_APPROVAL,
        Reversibility.IRREVERSIBLE,
        "DELIST via Seller Center (compensation only; does not erase platform "
        "violation records) — 03 §6.3",
        external_effect=True,
        grantable=False,
        approver_role="Operator",
        evidence_kinds=(
            EVIDENCE_ASSET_COMPARE,
            EVIDENCE_COMPLIANCE_REPORT,
            EVIDENCE_BACKTRANSLATION,
            EVIDENCE_PRICE_MARGIN,
            EVIDENCE_PAYLOAD_PREVIEW,
            EVIDENCE_WARN_LIST,
        ),
        preconditions=(
            "PC-PAYLOAD",
            "PC-FX",
            "PC-FX-FRESH",
            "PC-COST",
            "PC-PRICE-FLOOR",
            "PC-SOURCE",
            "PC-SOURCE-FRESH",
            "PC-RULES",
            "PC-G0",
            "PC-SHOP",
            "PC-DIRECTION",
            "PC-ASSET",
            "PC-TAX",
        ),
        guardrails=("daily_listing_cap", "price_floor"),
        required_facts=(
            "cost_snapshot",
            "fx_rate",
            "compliance_report",
            "license_evidence",
            "payload_hash",
        ),
        subject_type="listing_payload",
    ),
    # --- owner-only exceptions (04 §2.1) --------------------------------
    _spec(
        "ACT-RELEASE-COST-GATE",
        Disposition.HUMAN_APPROVAL,
        Reversibility.REVERSIBLE,
        "revoke the exception; generation stops at the budget again",
        grantable=False,
        approver_role="Owner",
        evidence_kinds=(
            EVIDENCE_BUDGET_USAGE,
            "trigger_item",
            EVIDENCE_DEGRADATION_PLAN,
        ),
        guardrails=("generation_budget",),
        required_facts=("budget_usage",),
        subject_type="generation_budget",
    ),
    _spec(
        "ACT-ACK-DISPATCH-RISK",
        Disposition.HUMAN_APPROVAL,
        Reversibility.REVERSIBLE,
        "withdraw the signature; the block comes back",
        grantable=False,
        approver_role="Owner",
        evidence_kinds=(
            EVIDENCE_RISK_STATEMENT,
            EVIDENCE_SOURCE_OF_VALUE,
            EVIDENCE_ALTERNATIVES,
        ),
        required_facts=("dispatch_days_value", "dispatch_days_source"),
        subject_type="shop_profile",
    ),
    _spec(
        "ACT-ACCEPT-MISMATCH",
        Disposition.HUMAN_APPROVAL,
        Reversibility.REVERSIBLE,
        "reopen the mismatch (the acceptance stays in the audit)",
        grantable=False,
        approver_role="Owner",
        preconditions=("PC-PAYLOAD",),
        required_facts=("readback_diff",),
        subject_type="listing_job",
    ),
    _spec(
        "ACT-LOOSEN-RULE",
        Disposition.HUMAN_APPROVAL,
        Reversibility.REVERSIBLE,
        "restore the previous value from the audit record",
        grantable=False,
        approver_role="Owner",
        evidence_kinds=(EVIDENCE_LOOSEN_DIFF, "effective_at", "rule_source"),
        subject_type="rule",
    ),
    # --- governance / configuration (HUMAN_INITIATED) --------------------
    _spec(
        "ACT-CREATE-GRANT",
        Disposition.HUMAN_INITIATED,
        Reversibility.REVERSIBLE,
        "revoke the grant",
        grantable=False,
        approver_role="Owner",
        depends_on_ruleset=False,
        subject_type="grant",
    ),
    _spec(
        "ACT-RULESET-PUBLISH",
        Disposition.HUMAN_INITIATED,
        Reversibility.REVERSIBLE,
        "publish a newer version",
        grantable=False,
        approver_role="Owner",
        depends_on_ruleset=False,
        subject_type="ruleset",
    ),
    _spec(
        "ACT-RULESET-RENEW",
        Disposition.HUMAN_INITIATED,
        Reversibility.REVERSIBLE,
        "let it expire again on the next review date",
        grantable=False,
        approver_role="Owner",
        depends_on_ruleset=False,
        subject_type="ruleset",
    ),
    _spec(
        "ACT-FETCH-DATA",
        Disposition.AUTO,
        Reversibility.REVERSIBLE,
        "discard the observation row",
        external_effect=True,
        subject_type="observation",
    ),
    _spec(
        "ACT-BUILD-BATCH",
        Disposition.AUTO,
        Reversibility.REVERSIBLE,
        "delete the generated pack",
        guardrails=("batch_max",),
        subject_type="listing_batch",
    ),
    _spec(
        "ACT-READBACK-IMPORT",
        Disposition.HUMAN_INITIATED,
        Reversibility.REVERSIBLE,
        "re-import the export file",
        approver_role="Operator",
        subject_type="listing_batch",
    ),
    _spec(
        "ACT-EXPORT-AUDIT",
        Disposition.HUMAN_INITIATED,
        Reversibility.REVERSIBLE,
        "the export cannot be recalled; the export itself is audited",
        approver_role="Owner",
        depends_on_ruleset=False,
        subject_type="audit_export",
    ),
    _spec(
        "ACT-DIRECTION-SAVE",
        Disposition.HUMAN_INITIATED,
        Reversibility.REVERSIBLE,
        "save the previous version again",
        approver_role="Owner",
        depends_on_ruleset=False,
        subject_type="direction",
    ),
    _spec(
        "ACT-SETTINGS-SAVE",
        Disposition.HUMAN_INITIATED,
        Reversibility.REVERSIBLE,
        "save the previous settings again",
        approver_role="Owner",
        depends_on_ruleset=False,
        subject_type="settings",
    ),
)

REGISTRY: Mapping[str, ActionSpec] = {spec.name: spec for spec in _ACTION_SPECS}

if len(REGISTRY) != len(_ACTION_SPECS):  # pragma: no cover - import-time guard
    raise RuntimeError("duplicate action name in the registry")

#: 04 §2.1: ACT-APPROVE-ASSETS is an alias used by the design text for the
#: consent-2 action; the registry stores only ACT-LIST-CREATE. Evidence for
#: consent 2 therefore hangs off ACT-LIST-CREATE.
APPROVE_ASSETS_ALIAS = "ACT-APPROVE-ASSETS"
CONSENT2_ACTION = "ACT-LIST-CREATE"

#: Actions that must not exist anywhere (04 §2.2, NV-2, NV-3).
FORBIDDEN_ACTION_NAMES: tuple[str, ...] = (
    "TRANSFER_FUNDS",
    "WITHDRAW",
    "CHANGE_PAYMENT_CYCLE",
    "DEPOSIT_OPERATION",
    "CLOSE_SHOP",
    "CHANGE_ENTITY",
    "CHANGE_ACCOUNT_PERMISSION",
    "SUBMIT_APPEAL",
    "FILE_TAX",
    "UPDATE_PRICE_ON_PLATFORM",
    "UPDATE_STOCK_ON_PLATFORM",
    "ACT-CREATE-ORDER",
    "ACT-HANDLE-AFTERSALE",
    "ACT-MANAGE-ADS",
    "ACT-MANAGE-AFFILIATE",
    "ACT-DELIST",  # P1.5 only (04 §2.1 note)
    "ACT-APPROVE-ASSETS",  # alias, never an executable action
)

# ---------------------------------------------------------------------------
# Tool catalog (05 §3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    action: str | None
    external_effect: bool = False
    #: Agents allowed to call the tool. Empty means "humans/system only".
    callers: frozenset[str] = frozenset()


def _tool(name: str, action: str | None, *, external: bool = False, callers: tuple[str, ...] = ()) -> ToolSpec:
    if action is not None and action not in REGISTRY:
        raise RuntimeError(f"tool {name} references unregistered action {action}")
    return ToolSpec(name=name, action=action, external_effect=external, callers=frozenset(callers))


_TOOLS: tuple[ToolSpec, ...] = (
    _tool("import.parse_file", "ACT-IMPORT-DATA", callers=("Scout",)),
    _tool("import.vision_extract", "ACT-IMPORT-DATA", external=True, callers=("Scout",)),
    _tool("candidates.upsert", "ACT-SCORE", callers=("Scout",)),
    _tool("costing.calc", "ACT-COST-CALC", callers=("Scout", "Checker")),
    _tool("g0.check", "ACT-COMPLIANCE-CHECK", callers=("Scout", "Checker")),
    _tool("score.run", "ACT-SCORE", callers=("Scout",)),
    _tool("collect.record", "ACT-COLLECT-RECORD", callers=("Sourcer",)),
    _tool("collect.dedupe", "ACT-COLLECT-RECORD", callers=("Sourcer",)),
    _tool("collect.ip_prescreen", "ACT-COLLECT-RECORD", callers=("Sourcer",)),
    _tool("llm.generate_text", "ACT-GENERATE-TEXT", external=True, callers=("Creator",)),
    _tool("image.render", "ACT-GENERATE-IMAGE", callers=("Creator",)),
    _tool("video.render", "ACT-GENERATE-VIDEO", callers=("Creator",)),
    _tool("tts.synthesize", "ACT-GENERATE-VIDEO", external=True, callers=("Creator",)),
    _tool("compliance.check", "ACT-COMPLIANCE-CHECK", callers=("Creator", "Checker")),
    # approval.decide exists as a service entry point but is never a tool an
    # agent can call: `callers` is empty and the Gate refuses agent actors.
    _tool("approval.create", None, callers=("Pilot",)),
    _tool("approval.decide", None),
    # 05 §3 maps this tool to ACT-BUILD-CHECKLIST (AUTO), but 04 §5.2 states
    # "the checklist and the asset pack must not be downloadable before
    # approval". Mapping the tool to the gated ACT-LIST-CREATE is the stricter
    # reading (00 §2); the AUTO action stays registered for pack assembly.
    _tool("listing.build_checklist", "ACT-LIST-CREATE", callers=("Lister",)),
    _tool("listing.compare_readback", "ACT-READBACK-COMPARE", callers=("Lister", "Checker")),
    _tool("connector.fetch", "ACT-FETCH-DATA", external=True),
    _tool("batch.build_pack", "ACT-BUILD-BATCH", callers=("Lister",)),
    _tool("readback.import_export", "ACT-READBACK-IMPORT"),
    _tool("notify.send", None, callers=("Pilot",)),
)

TOOL_CATALOG: Mapping[str, ToolSpec] = {tool.name: tool for tool in _TOOLS}
if len(TOOL_CATALOG) != len(_TOOLS):  # pragma: no cover - import-time guard
    raise RuntimeError("duplicate tool name in the catalog")

#: 05 §3.1 agent x tool matrix, as data.
AGENT_TOOL_WHITELIST: Mapping[str, frozenset[str]] = {
    "Pilot": frozenset({"approval.create", "notify.send"}),
    "Scout": frozenset(
        {
            "import.parse_file",
            "import.vision_extract",
            "candidates.upsert",
            "costing.calc",
            "g0.check",
            "score.run",
        }
    ),
    "Sourcer": frozenset({"collect.record", "collect.dedupe", "collect.ip_prescreen"}),
    "Creator": frozenset(
        {
            "llm.generate_text",
            "image.render",
            "video.render",
            "tts.synthesize",
            "compliance.check",
        }
    ),
    "Lister": frozenset(
        {
            "listing.build_checklist",
            "listing.compare_readback",
            "batch.build_pack",
        }
    ),
    "Checker": frozenset(
        {
            "costing.calc",
            "g0.check",
            "compliance.check",
            "listing.compare_readback",
        }
    ),
}

ROLE_OWNER = "Owner"
ROLE_OPERATOR = "Operator"
ROLES: frozenset[str] = frozenset({ROLE_OWNER, ROLE_OPERATOR})


def get_spec(action_name: str) -> ActionSpec:
    """Return the spec or raise ``KeyError``; callers convert it to ACTION_FORBIDDEN."""
    return REGISTRY[action_name]


def spec_or_none(action_name: str) -> ActionSpec | None:
    return REGISTRY.get(action_name)


def evidence_kinds(action_name: str) -> tuple[str, ...]:
    """Evidence for an action; resolves the ACT-APPROVE-ASSETS alias of 04 §4.2."""
    if action_name == APPROVE_ASSETS_ALIAS:
        action_name = CONSENT2_ACTION
    spec = REGISTRY.get(action_name)
    return spec.evidence_kinds if spec else ()


def is_grantable(action_name: str) -> bool:
    spec = REGISTRY.get(action_name)
    return bool(spec and spec.grantable)


__all__ = [
    "AGENT_TOOL_WHITELIST",
    "APPROVE_ASSETS_ALIAS",
    "ActionSpec",
    "CONSENT2_ACTION",
    "FORBIDDEN_ACTION_NAMES",
    "REGISTRY",
    "ROLES",
    "ROLE_OPERATOR",
    "ROLE_OWNER",
    "TOOL_CATALOG",
    "ToolSpec",
    "evidence_kinds",
    "get_spec",
    "is_grantable",
    "spec_or_none",
]
