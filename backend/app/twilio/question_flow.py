"""question_flow.py - Defines the multi-question mental-health check-in call flow.

Each question dict has:
  id         : 0-based index (used in webhook URL paths /voice/respond/{id})
  text       : Text spoken via Twilio TTS before the recording starts
  type       : always 'record' — all questions collect a voice recording
  timeout    : seconds of silence after which Twilio stops recording
  max_length : maximum recording length in seconds

Modify, add, or remove questions here without changing any other file.
"""

from typing import Any, Dict, List

QUESTIONS: List[Dict[str, Any]] = [
    # ── Q0: Overall day feeling ────────────────────────────────────────────────
    {
        "id": 0,
        "text": (
            "Hello! This is an automated call from IIT Gandhinagar for research purposes. You have been randomly selected to participate. Your responses are confidential. The call will last about 3 minutes, and please respond after each beep. Thank you for participating!"

            "Perhaps You can describe your typical day and tell me about the parts you actually enjoy."
        ),
        "type": "record",
        "timeout": 7,
        "max_length": 180,
    },
    # ── Q1: Emotions ───────────────────────────────────────────────────────────
    {
        "id": 1,
        "text": (
            "Perhaps You can talk about your take on campus events and whether you're someone who usually joins in or skips out."
        ),
        "type": "record",
        "timeout": 7,
        "max_length": 180,
    },
    # ── Q2: Productivity ───────────────────────────────────────────────────────
    {
        "id": 2,
        "text": (
            "Question 3: Share your favourite college memory so far and what made it so special. "
        ),
        "type": "record",
        "timeout": 7,
        "max_length": 180,
    },
    # ── Q3: Overthinking ──────────────────────────────────────────────────────
    {
        "id": 3,
        "text": (
            "Question 4: Tell me about how you and your friends hang out and have fun outside of class. "
        ),
        "type": "record",
        "timeout": 7,
        "max_length": 180,
    },
    # ── Q4: Energy drain ───────────────────────────────────────────────────────
    {
        "id": 4,
        "text": (
            "Question 5: Mention any clubs you're in and the best thing about being a part of them. "
        ),
        "type": "record",
        "timeout": 7,
        "max_length": 180,
    },
    # ── Q5: Social connection ──────────────────────────────────────────────────
    {
        "id": 5,
        "text": (
            "Question 6: Feel free to share anything else on your mind about your college experience or personal life things."
        ),
        "type": "record",
        "timeout": 7,
        "max_length": 180,
    },
]

TOTAL_QUESTIONS: int = len(QUESTIONS)

CLOSING_MESSAGE: str = (
    "Thank you for answering our questions. "
    "Your responses have been recorded and will be reviewed by your counsellor. "
    "Take care, and goodbye."
)

NO_INPUT_MESSAGE: str = (
    "We did not receive your input. Moving to the next question."
)


def get_question(index: int) -> Dict[str, Any]:
    """Return the question at *index*, or raise IndexError."""
    return QUESTIONS[index]


def is_last_question(index: int) -> bool:
    return index >= TOTAL_QUESTIONS - 1
