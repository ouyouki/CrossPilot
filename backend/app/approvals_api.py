"""审批中心的接口:看单、记"已查看"、批/退回/拒绝。

判定仍在 `04` 内核:`ApprovalsService.decide` 要求"人的身份 + 版本 + 载荷哈希 + 必看证据",
这里只做 HTTP 形状与错误码,不重写规则。
"""

from __future__ import annotations

from typing import Any

from crosspilot.approvals.service import ApprovalDecision
from crosspilot.audit.log import AuditDecision
from crosspilot.core.errors import ToolGateError

from . import handlers, store

ACTOR = store.OPERATOR


class ApprovalNotFound(LookupError):
    pass


def _approval(approval_id: str):
    try:
        return store.repo.get(approval_id)
    except KeyError as error:
        raise ApprovalNotFound(f"没有这张审批单:{approval_id}") from error


def _evidence(subject_refs: tuple[str, ...]) -> list[dict[str, Any]]:
    rows = {row["id"]: row for row in handlers.candidates()["items"]}
    cards = []
    for ref in subject_refs:
        row = rows.get(ref)
        if row is None:
            cards.append({"id": ref, "status": "UNKNOWN", "missing": ["候选不在样例数据里"]})
            continue
        cards.append(
            {
                "id": row["id"],
                "title": row["title"],
                "category": row["category"],
                "price_jpy": row["price_jpy"],
                "status": row["status"],
                "revenue": row["revenue"],
                "profit": row["profit"],
                "margin": row["margin"],
                "missing": row["missing"],
                "cost_items": row["cost_items"],
            }
        )
    return cards


def detail(approval_id: str) -> dict[str, Any]:
    approval = _approval(approval_id)
    return {
        "id": approval.id,
        "action_type": approval.action_type,
        "title": approval.title,
        "status": approval.status.value,
        "version": approval.version,
        "payload_hash": approval.payload_hash,
        "subject_refs": list(approval.subject_refs),
        "required_viewed": list(approval.required_viewed),
        "viewed": sorted(store.service.viewed_sections(approval.id)),
        "created_at": approval.created_at.isoformat() if approval.created_at else None,
        "evidence": _evidence(approval.subject_refs),
        "persistence": "memory",
    }


def record_view(approval_id: str, section: str) -> dict[str, Any]:
    _approval(approval_id)
    if not section:
        raise ValueError("section 不能为空")
    viewed = store.service.record_view(approval_id, user_id=ACTOR.id, section=section)
    return {"id": approval_id, "viewed": sorted(viewed)}


def decide(approval_id: str, body: dict[str, Any]) -> dict[str, Any]:
    _approval(approval_id)
    raw = str(body.get("decision", "")).upper()
    try:
        decision = ApprovalDecision(raw)
    except ValueError as error:
        raise ToolGateError("ACTION_FORBIDDEN", f"未知的决定:{raw!r}") from error

    try:
        version = int(body.get("version"))
    except (TypeError, ValueError) as error:
        raise ToolGateError("VERSION_CONFLICT", "缺少 version") from error

    updated = store.service.decide(
        approval_id,
        actor=ACTOR,
        if_match_version=version,
        payload_hash=str(body.get("payload_hash", "")),
        decision=decision,
        now=store.clock.now(),
        note=str(body.get("note", "")),
        return_reason_code=body.get("return_reason_code"),
    )
    store.record(
        "ACT-SELECT",
        approval_id,
        AuditDecision.ALLOWED,
        {"decision": decision.value, "status": updated.status.value},
    )
    return {
        "id": updated.id,
        "status": updated.status.value,
        "version": updated.version,
        "approver_user_id": updated.approver_user_id,
        "approver_kind": updated.approver_kind,
    }


__all__ = ["ApprovalNotFound", "decide", "detail", "record_view"]
