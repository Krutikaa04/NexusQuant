"""Strategy Management & Orchestration Core — the central bounded context of NexusQuant.

A Strategy is a production asset with a governed lifecycle, versioned configuration,
mutable operational health, and a full audit trail. Every other context consumes Strategy;
this context owns it. Execution, paper/live trading, portfolio, risk, and AI are out of
scope here and live in downstream contexts.
"""
