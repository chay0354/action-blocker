"""
Kernel - Deterministic Decision Layer for Action Blocker
Evaluates context and returns "N" (allow) or "L" (limit/block)
Implements Hard-Stop rules: timeout, agent_error -> "L"
"""
from typing import Dict, Any, Literal

Decision = Literal["N", "L"]


def evaluate(context: Dict[str, Any]) -> Decision:
    """
    Evaluate context and return kernel decision.
    "N" = No block (allow), "L" = Limit (block)

    Hard-Stop rules (any triggers "L"):
    - agent_error: Agent/RulesEngine raised an error
    - timeout: Request timed out

    Normal flow: uses agent result (needs_approval/violations)
    """
    # Hard-Stop: agent error -> block
    if context.get("agent_error"):
        return "L"

    # Hard-Stop: timeout -> block
    if context.get("timeout"):
        return "L"

    # Normal flow: agent says needs_approval (has violations) -> block
    needs_approval = context.get("needs_approval", False)
    if needs_approval:
        return "L"

    # No violations, no hard-stop -> allow
    return "N"
