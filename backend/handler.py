"""Zappa handler module for Docker container Lambda deployments.

In zip deployments, Zappa auto-generates this file. For container image
deployments, we provide it manually.

Zappa's event dispatcher imports this module when handling scheduled
events (e.g., keep-warm). The event rule ARN is parsed to derive
"handler.keep_warm_callback", so this module must be importable.
"""

from typing import Any


def keep_warm_callback(
    event: dict[str, Any] | None = None,
    context: Any | None = None,
) -> dict[str, Any]:
    """Handle Zappa keep-warm events to prevent cold starts."""
    return {}
