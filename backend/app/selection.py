"""同意 1(选品同意)的处理器:纯函数 + 模块级内存状态,便于测试。"""

from __future__ import annotations

from typing import Any

from crosspilot.approvals.model import Approval
from crosspilot.approvals.state_machine import ApprovalStatus
from crosspilot.audit.log import AuditDecision

from . import store


class SelectionError(ValueError):
    """可以如实告诉用户的拒绝原因(上限、未知候选、空选)。"""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def approvals() -> dict[str, Any]:
    items = [
        {
            "id": approval.id,
            "action_type": approval.action_type,
            "status": approval.status.value,
            "subject_refs": list(approval.subject_refs),
            "title": approval.title,
            "created_at": approval.created_at.isoformat() if approval.created_at else None,
        }
        for approval in _pending_only(store.open_approvals())
    ]
    return {"items": items, "count": len(items), "persistence": "memory"}


def _pending_only(approvals: list) -> list:
    """待批 = PENDING。APPROVED 还没执行,但它已经不是"等你批"了。"""
    from crosspilot.approvals.state_machine import ApprovalStatus

    return [a for a in approvals if a.status is ApprovalStatus.PENDING]


def create_selection(subject_refs: list[str]) -> dict[str, Any]:
    """勾选若干候选 → 生成一张 ACT-SELECT 审批单(挂起等批)。

    这里不判"该不该批"——判定是 Gatekeeper 的事,同意 1 的处置就是 REQUIRE_HUMAN,
    所以本函数只负责把人选出来的东西变成一张待批单。
    """
    ids = [str(x).strip() for x in subject_refs if str(x).strip()]
    if not ids:
        raise SelectionError("EMPTY_SELECTION", "没有勾选任何候选")
    if len(set(ids)) != len(ids):
        raise SelectionError("DUPLICATE_SUBJECT", "同一批里有重复的候选")
    if len(ids) > store.SELECTION_CAP:
        raise SelectionError("OVER_CAP", f"单批最多勾选 {store.SELECTION_CAP} 个,收到 {len(ids)} 个")

    known = {row["id"] for row in _candidates()}
    unknown = [x for x in ids if x not in known]
    if unknown:
        raise SelectionError("UNKNOWN_SUBJECT", f"候选不存在:{', '.join(unknown)}")

    existing = store.find_selection(tuple(ids))
    if existing is not None:
        store.record(
            "ACT-SELECT",
            ",".join(ids),
            AuditDecision.ALLOWED,
            {"result": "duplicate", "approval_id": existing.id},
        )
        return {"approval_id": existing.id, "status": existing.status.value, "duplicate": True}

    approval = Approval.new(
        approval_id=f"ap-select-{len(store.open_approvals()) + 1}",
        shop_id=store.SHOP_ID,
        action_type="ACT-SELECT",
        subject_refs=tuple(ids),
        now=store.clock.now(),
        title=f"同意 1:选品 {len(ids)} 个候选",
        required_viewed=("cost_breakdown", "g0_verdict", "demand_signal"),
    )
    store.service.create(approval)
    submitted = store.service.submit(approval.id, now=store.clock.now())
    store.record(
        "ACT-SELECT",
        ",".join(ids),
        AuditDecision.ALLOWED,
        {"result": "created", "approval_id": submitted.id},
    )
    return {
        "approval_id": submitted.id,
        "status": submitted.status.value,
        "duplicate": False,
        "required_viewed": list(submitted.required_viewed),
    }


def _candidates() -> list[dict[str, Any]]:
    from . import handlers

    return handlers.candidates()["items"]


__all__ = [
    "ApprovalStatus",
    "SelectionError",
    "approvals",
    "create_selection",
]
