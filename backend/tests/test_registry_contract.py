"""Domain invariants that do not map to a single INV number.

These are the contract details the engine relies on elsewhere: undo paths are
declared, the registry and the tool catalog cannot drift apart, and the consent-2
alias resolves to the action that actually exists.
"""

from __future__ import annotations

import unittest

from crosspilot.core.decision import Disposition, Reversibility
from crosspilot.registry.actions import (
    AGENT_TOOL_WHITELIST,
    APPROVE_ASSETS_ALIAS,
    CONSENT2_ACTION,
    EVIDENCE_COMPLIANCE_REPORT,
    REGISTRY,
    TOOL_CATALOG,
    evidence_kinds,
)


class RegistryContract(unittest.TestCase):
    def test_every_action_declares_an_undo_path(self):
        for name, spec in REGISTRY.items():
            with self.subTest(name=name):
                self.assertTrue(spec.undo.strip(), f"{name} has no undo text")
                if spec.reversibility is Reversibility.IRREVERSIBLE:
                    # 04 §2.1 describes a compensation for consent 2, so the
                    # text must say so rather than pretend it is reversible.
                    self.assertTrue(spec.external_effect or spec.undo, name)

    def test_irreversible_actions_are_external(self):
        for name, spec in REGISTRY.items():
            if spec.reversibility is Reversibility.IRREVERSIBLE:
                with self.subTest(name=name):
                    self.assertTrue(spec.external_effect, f"{name} is irreversible but internal")

    def test_tool_catalog_references_registered_actions(self):
        for tool in TOOL_CATALOG.values():
            if tool.action is None:
                continue
            self.assertIn(tool.action, REGISTRY)

    def test_agent_whitelists_reference_known_tools(self):
        for agent, tools in AGENT_TOOL_WHITELIST.items():
            for tool in tools:
                with self.subTest(agent=agent, tool=tool):
                    self.assertIn(tool, TOOL_CATALOG)

    def test_consent2_alias_resolves_to_the_real_action(self):
        self.assertEqual(CONSENT2_ACTION, "ACT-LIST-CREATE")
        self.assertNotIn(APPROVE_ASSETS_ALIAS, REGISTRY)
        self.assertIn(EVIDENCE_COMPLIANCE_REPORT, evidence_kinds(APPROVE_ASSETS_ALIAS))
        self.assertIn(EVIDENCE_COMPLIANCE_REPORT, evidence_kinds(CONSENT2_ACTION))

    def test_consent2_is_operator_only_and_never_grantable(self):
        spec = REGISTRY[CONSENT2_ACTION]
        self.assertEqual(spec.approver_role, "Operator")
        self.assertFalse(spec.grantable)
        self.assertEqual(spec.disposition, Disposition.HUMAN_APPROVAL)
        self.assertTrue(spec.external_effect)

    def test_consent1_is_the_only_grantable_action(self):
        grantable = [name for name, spec in REGISTRY.items() if spec.grantable]
        self.assertEqual(grantable, ["ACT-SELECT"])

    def test_human_initiated_actions_do_not_need_a_fresh_ruleset_when_governance(self):
        for name in (
            "ACT-RULESET-RENEW",
            "ACT-RULESET-PUBLISH",
            "ACT-CREATE-GRANT",
            "ACT-DIRECTION-SAVE",
            "ACT-SETTINGS-SAVE",
        ):
            with self.subTest(name=name):
                self.assertFalse(REGISTRY[name].depends_on_ruleset)


if __name__ == "__main__":
    unittest.main()
