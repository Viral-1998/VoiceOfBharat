"""Telephony and Outbound Call package for Day 6 (#VoiceForBharat)."""

from .outbound import OutboundCallManager, calculate_next_retry, trigger_outbound_call

__all__ = ["OutboundCallManager", "calculate_next_retry", "trigger_outbound_call"]
