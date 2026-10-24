"""CrossPilot deterministic core.

This package implements design volumes 04 (approval & gate engine) and the
parts of 01/06 they depend on. It deliberately has **no runtime dependencies**
beyond the standard library: the design requires the decision path to be free of
LLM, network and framework coupling (INV-8), and the core must stay testable
without PostgreSQL while the persistence layer is still being built.

Import order of authority when documents disagree: 01 red lines > 04 engine >
everything else (design/ai/00_AI读我.md §2).
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
