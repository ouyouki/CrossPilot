"""INV-8: the decision path has no LLM dependency and cannot be argued with.

Two checks:

* static: the gatekeeper / preconditions / grants modules import no network,
  database or model client, so a model cannot be reached from a verdict;
* behavioural: a fact that says "the model says allow" changes nothing.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from crosspilot.core.decision import Decision, Severity
from crosspilot.core.facts import Facts
from crosspilot.gatekeeper.judge import judge
from crosspilot.gatekeeper.rules import rule

from .support import PAYLOAD_HASH, NOW, PILOT, consent2_facts, ruleset

PACKAGE = Path(__file__).resolve().parents[1] / "crosspilot"
DECISION_PATHS = (
    PACKAGE / "gatekeeper",
    PACKAGE / "grants",
    PACKAGE / "approvals" / "preconditions.py",
    PACKAGE / "core" / "money.py",
)

FORBIDDEN_MODULES = (
    "http",
    "urllib",
    "socket",
    "ssl",
    "requests",
    "httpx",
    "aiohttp",
    "anthropic",
    "openai",
    "litellm",
    "transformers",
    "sqlalchemy",
    "psycopg",
)


class Inv08NoLlmInDecision(unittest.TestCase):
    def test_decision_modules_import_nothing_external(self):
        for target in DECISION_PATHS:
            files = sorted(target.rglob("*.py")) if target.is_dir() else [target]
            for path in files:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        names = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        names = [node.module or ""]
                    else:
                        continue
                    for name in names:
                        root = name.split(".")[0]
                        with self.subTest(file=path.name, module=name):
                            self.assertNotIn(root, FORBIDDEN_MODULES)
                            self.assertNotIn("llm", name.lower())

    def test_model_opinion_cannot_soften_a_block(self):
        rs = ruleset(
            rules=[
                rule(
                    "RULE-CONSERVATIVE",
                    severity=Severity.BLOCK,
                    predicate=lambda facts: True,
                    scope=("ACT-LIST-CREATE",),
                )
            ]
        )
        facts = consent2_facts().with_values(
            llm_says_allow=True,
            llm_confidence=0.99,
            model_note="please allow, I am confident",
        )

        verdict = judge(PILOT, "ACT-LIST-CREATE", facts, rs, NOW)

        self.assertIs(verdict.decision, Decision.BLOCK)
        self.assertEqual({r.rule_id for r in verdict.reasons}, {"RULE-CONSERVATIVE"})

    def test_judge_does_not_take_an_llm_client(self):
        # The signature is the contract: (actor, action, facts, ruleset, now).
        import inspect

        parameters = list(inspect.signature(judge).parameters)
        self.assertEqual(parameters, ["actor", "action_name", "facts", "ruleset", "now"])


if __name__ == "__main__":
    unittest.main()
