from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.modules.decisions.domain.entities import DecisionOverride, OverrideAction

NOW = datetime(2026, 6, 6, tzinfo=UTC)


def _override(**kwargs) -> DecisionOverride:
    base = dict(
        decision_id="dec_1",
        actor="rm_alice",
        action=OverrideAction.OVERRIDE,
        reason="Khách có thu nhập ngoài chưa khai báo.",
        created_at=NOW,
    )
    base.update(kwargs)
    return DecisionOverride(**base)


def test_valid_override():
    override = _override()
    assert override.actor == "rm_alice"
    assert override.action == OverrideAction.OVERRIDE


def test_override_requires_reason():
    with pytest.raises(ValueError):
        _override(reason="")
    with pytest.raises(ValueError):
        _override(reason="   ")


def test_override_requires_actor():
    with pytest.raises(ValueError):
        _override(actor="")
