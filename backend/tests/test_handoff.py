import pytest
from livekit.agents import AgentSession, inference, llm

from agent import ClinicAppointmentSpecialist, HealthAccessAssistant


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
async def test_normal_question_stays_with_main_agent() -> None:
    """Evaluation: Normal health query stays with main agent (Arogya Seva)."""
    async with (
        _llm() as llm_inst,
        AgentSession(llm=llm_inst) as session,
    ):
        await session.start(HealthAccessAssistant())

        result = await session.run(
            user_input="What simple home remedies can I use for a mild sore throat?"
        )

        await _get_assistant_message(result).judge(
            llm_inst,
            intent="""
            Provides helpful, simple home care guidance for a sore throat (e.g. warm water, gargling, rest).
            Stays as Arogya Seva main assistant and does NOT attempt to hand off to an appointment specialist.
            """,
        )


@pytest.mark.asyncio
async def test_appointment_question_hands_off_to_specialist() -> None:
    """Evaluation: Doctor appointment booking request triggers handoff to Clinic Specialist."""
    async with (
        _llm() as llm_inst,
        AgentSession(llm=llm_inst) as session,
    ):
        await session.start(HealthAccessAssistant())

        result = await session.run(
            user_input="I want to book an OPD doctor appointment at Pune PHC for tomorrow morning."
        )

        await _get_assistant_message(result).judge(
            llm_inst,
            intent="""
            Acknowledges the appointment booking request.
            Announces connecting or handing off to the clinic and appointment specialist, or books the clinic slot through the specialist.
            """,
        )


@pytest.mark.asyncio
async def test_specialist_handles_booking() -> None:
    """Evaluation: Specialist agent directly handles OPD clinic appointment booking."""
    async with (
        _llm() as llm_inst,
        AgentSession(llm=llm_inst) as session,
    ):
        await session.start(ClinicAppointmentSpecialist())

        result = await session.run(
            user_input="Please book an OPD doctor appointment for Ramesh at Aundh PHC tomorrow at 10:00 AM."
        )

        await _get_assistant_message(result).judge(
            llm_inst,
            intent="""
            Confirms the OPD doctor appointment booking for Ramesh.
            Provides the appointment booking details or Reference ID clearly.
            """,
        )


@pytest.mark.asyncio
async def test_specialist_hands_back_on_general_query() -> None:
    """Evaluation: Specialist agent hands back to main assistant on general health query."""
    async with (
        _llm() as llm_inst,
        AgentSession(llm=llm_inst) as session,
    ):
        await session.start(ClinicAppointmentSpecialist())

        result = await session.run(
            user_input="Can you give me advice on what to do for severe chest pain?"
        )

        await _get_assistant_message(result).judge(
            llm_inst,
            intent="""
            Recognizes severe chest pain as an emergency.
            Advises seeking immediate emergency medical help/calling emergency services (or 108) and/or hands back to the main emergency health assistant.
            """,
        )
