import os
import sys

import pytest
from livekit.agents import AgentSession, inference, llm

# Ensure backend/src is in sys.path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

import db
from agent import Assistant
from telephony.outbound import OutboundCallManager, calculate_next_retry


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


def _get_assistant_message(result):
    """Consume tool call events if any, until ChatMessageEvent for assistant is found."""
    while True:
        event = result.expect.next_event()
        try:
            return event.is_message(role="assistant")
        except AssertionError:
            continue


@pytest.mark.asyncio
async def test_opt_out_tool_execution() -> None:
    """Evaluation of the agent's opt-out tool execution when user requests to unsubscribe."""
    test_phone = "+919998887770"
    db.init_db()

    async with (
        _llm() as llm_inst,
        AgentSession(llm=llm_inst) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=f"Please opt me out of these calls. Stop calling {test_phone}."
        )

        await _get_assistant_message(result).judge(
            llm_inst,
            intent="""
            Acknowledges the user's request to opt out or stop receiving calls.
            Confirms that they have been unsubscribed or opted out gracefully.
            """,
        )

    # Verify database state
    assert db.is_opted_out(test_phone) or db.is_opted_out("default_caller")


@pytest.mark.asyncio
async def test_native_script_hindi_response() -> None:
    """Evaluation that Hindi responses adhere to native Devanagari script (not romanized)."""
    async with (
        _llm() as llm_inst,
        AgentSession(llm=llm_inst) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="नमस्ते, मेरी दवा का समय क्या है? कृपया हिंदी में बताएं।"
        )

        await _get_assistant_message(result).judge(
            llm_inst,
            intent="""
            Responds in Hindi using native Devanagari script (such as नमस्ते or स्वास्थ्य).
            Does not use romanized Hindi words like 'namaste' or 'dawa'.
            """,
        )


def test_outcome_retry_calculations() -> None:
    """Verify outcome handling retry calculations for no_answer, busy, voicemail, hangup, and opt_out."""
    # 1. No answer -> ~15 mins delay
    retry_no_answer = calculate_next_retry("no_answer", current_retry_count=0)
    assert retry_no_answer is not None

    # 2. Busy -> ~5 mins delay
    retry_busy = calculate_next_retry("busy", current_retry_count=0)
    assert retry_busy is not None

    # 3. Voicemail -> No retry
    retry_voicemail = calculate_next_retry("voicemail", current_retry_count=0)
    assert retry_voicemail is None

    # 4. Immediate hangup -> ~30 mins delay
    retry_hangup = calculate_next_retry("immediate_hangup", current_retry_count=0)
    assert retry_hangup is not None

    # 5. Opt-out -> No retry
    retry_opt_out = calculate_next_retry("opt_out", current_retry_count=0)
    assert retry_opt_out is None

    # 6. Max retries exceeded -> No retry
    retry_max = calculate_next_retry("no_answer", current_retry_count=3)
    assert retry_max is None


def test_outbound_manager_eligibility() -> None:
    """Verify OutboundCallManager checks opt-out registry before placing call."""
    manager = OutboundCallManager()
    phone = "+919111122222"

    # Initially eligible
    eligible, _ = manager.can_place_call(phone)
    assert eligible is True

    # Register opt-out
    db.register_opt_out(phone, reason="Test opt out")

    # Now ineligible
    eligible_after, reason = manager.can_place_call(phone)
    assert eligible_after is False
    assert "opted out" in reason
