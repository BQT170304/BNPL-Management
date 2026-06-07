import json

from app.modules.advisory.application.dto import OptionPacket, ScoringPacket
from app.modules.advisory.domain.options import PaymentOption, PlanType
from app.modules.advisory.domain.subscores import SubScores
from app.modules.explanation.infrastructure.bedrock_scorer import BedrockScorer
from app.modules.explanation.infrastructure.hard_rule_scorer import HardRuleScorer


def _packet() -> ScoringPacket:
    inst = PaymentOption("installment_12", "Trả góp 12", PlanType.INSTALLMENT, 12, 1_250_000, 0)
    return ScoringPacket(
        profile_id="p1", risk_tolerance="MEDIUM",
        current_ncf=1_200_000, current_dti=37.9, current_efr=2.94, current_pgrs=100.0,
        item_name="Phone", purchase_amount=15_000_000,
        options=[OptionPacket(inst, 1_250_000, -50_000, 46.5, 2.94, 100.0, 8.0,
                              SubScores(20, 76.0, 30, 0))],
    )


class _StubClient:
    def __init__(self, body: str | None, raise_exc: Exception | None = None):
        self._body = body
        self._raise = raise_exc

    def invoke_model(self, **kwargs):
        if self._raise:
            raise self._raise
        return {"body": _StubBody(self._body)}


class _StubBody:
    def __init__(self, body: str | None):
        self._body = body

    def read(self) -> bytes:
        payload = {"content": [{"type": "text", "text": self._body}]}
        return json.dumps(payload).encode()


def test_bedrock_parses_valid_json():
    valid = json.dumps({
        "options": [{"option_id": "installment_12", "risk_score": 55,
                     "recommended": True, "explanation": "ổn", "key_factors": ["x"]}],
        "best_option_id": "installment_12", "summary": "ok",
    })
    scorer = BedrockScorer(client=_StubClient(valid), model_id="m", fallback=HardRuleScorer())
    result = scorer.score(_packet())
    assert result.scorer_used == "bedrock"
    assert result.options[0].risk_score == 55


def test_bedrock_malformed_json_falls_back():
    scorer = BedrockScorer(client=_StubClient("not json"), model_id="m", fallback=HardRuleScorer())
    result = scorer.score(_packet())
    assert result.scorer_used == "hard_rules"


def test_bedrock_client_error_falls_back():
    scorer = BedrockScorer(
        client=_StubClient(None, raise_exc=RuntimeError("boom")),
        model_id="m", fallback=HardRuleScorer(),
    )
    result = scorer.score(_packet())
    assert result.scorer_used == "hard_rules"
