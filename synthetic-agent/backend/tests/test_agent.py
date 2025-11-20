# backend/tests/test_agent.py
import pytest
from agent import AIMLAgent

@pytest.mark.parametrize("msg", ["hello", "how to train a model", "thanks"])
def test_agent_basic(msg):
    agent = AIMLAgent()
    resp = agent.respond(msg, user_id="test-user")
    assert isinstance(resp, str)
    assert len(resp) > 0\n