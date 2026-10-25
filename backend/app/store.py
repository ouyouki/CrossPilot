"""应用层的内存状态:审批单仓库 + 审计 + 选品上限。

为什么先放内存:`04` 内核的仓储接口已经有了,但没有数据库迁移。本阶段只要"点得动、链路真",
重启清空这件事会在页面上明说。等做持久化时把这个模块换成 SQL 实现即可,处理器不动。
"""

from __future__ import annotations

from crosspilot.approvals.repo import InMemoryApprovalRepo
from crosspilot.approvals.service import ApprovalsService
from crosspilot.audit.log import AuditDecision, AuditLog
from crosspilot.core.actors import Actor
from crosspilot.core.clock import SystemClock

SHOP_ID = "shop-1"
OPERATOR = Actor.human("u-operator", "Operator")
SELECTION_CAP = 10  # 03 §2.1 的 selection_cap 默认值;方向卡做出来之后改从配置读

clock = SystemClock()
repo = InMemoryApprovalRepo()
service = ApprovalsService(repo, clock)
audit = AuditLog()


def open_approvals() -> list:
    return sorted(repo.list_open(shop_id=SHOP_ID), key=lambda a: a.created_at or clock.now())


def find_selection(subject_refs: tuple[str, ...]):
    from crosspilot.approvals.model import subject_key

    key = subject_key(subject_refs)
    for approval in open_approvals():
        if approval.action_type == "ACT-SELECT" and approval.subject_key == key:
            return approval
    return None


def record(event_action: str, target: str, decision: AuditDecision, details: dict) -> None:
    audit.append(
        ts=clock.now(),
        actor_type=OPERATOR.kind,
        actor_id=OPERATOR.id,
        action=event_action,
        target=target,
        decision=decision,
        details=details,
    )
