from app.core.config import Settings


def test_defaults_use_memory_and_disabled_bedrock(monkeypatch):
    monkeypatch.delenv("PERSISTENCE", raising=False)
    monkeypatch.delenv("BEDROCK_ENABLED", raising=False)
    s = Settings(_env_file=None)
    assert s.persistence == "memory"
    assert s.bedrock_enabled is False
    assert s.allocation_strategy in ("weighted", "even")


def test_weights_loaded():
    s = Settings(_env_file=None)
    assert abs(s.score_weight_cashflow + s.score_weight_goal
               + s.score_weight_efr + s.score_weight_dti - 1.0) < 1e-9


def test_ingestion_and_cors_defaults():
    s = Settings(_env_file=None)
    assert s.ingestion_csv_path == "summary_by_cif_month.csv"
    assert s.cors_origins == "http://localhost:5173"
    assert s.cors_origin_list == ["http://localhost:5173"]
