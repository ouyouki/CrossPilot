"""INV-12: the actions that must never exist are absent everywhere."""

from __future__ import annotations

import unittest

from crosspilot.registry.actions import (
    AGENT_TOOL_WHITELIST,
    FORBIDDEN_ACTION_NAMES,
    REGISTRY,
    TOOL_CATALOG,
)


class Inv12ForbiddenActionsAbsent(unittest.TestCase):
    def test_forbidden_names_are_not_registered(self):
        for name in FORBIDDEN_ACTION_NAMES:
            with self.subTest(name=name):
                self.assertNotIn(name, REGISTRY)
                self.assertNotIn(name, {tool.action for tool in TOOL_CATALOG.values()})
                self.assertNotIn(name, TOOL_CATALOG)

    def test_money_and_legal_domains_are_absent(self):
        # NV-2 / NV-3: no tool exists in these areas at all, not even a disabled one.
        banned_fragments = (
            "withdraw",
            "transfer",
            "payment_cycle",
            "deposit",
            "close_shop",
            "entity",
            "permission",
            "appeal",
            "tax",
            "order.create",
            "refund",
        )
        haystack = " ".join(TOOL_CATALOG).lower() + " " + " ".join(REGISTRY).lower()
        for fragment in banned_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, haystack)

    def test_no_agent_may_decide(self):
        for agent, tools in AGENT_TOOL_WHITELIST.items():
            with self.subTest(agent=agent):
                self.assertNotIn("approval.decide", tools)

    def test_undeclared_action_never_reaches_the_registry_by_accident(self):
        for name in REGISTRY:
            self.assertTrue(name.startswith("ACT-"), name)


if __name__ == "__main__":
    unittest.main()
