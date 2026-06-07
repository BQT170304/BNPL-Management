from __future__ import annotations

import pytest

from app.modules.copilot.domain.intents import CopilotTool, parse_intent


@pytest.mark.parametrize(
    "message,tool",
    [
        ("Tôi có nên mua điện thoại 20 triệu trả góp 6 tháng không?", CopilotTool.RECOMMEND),
        ("Cho mình xem dự báo dòng tiền", CopilotTool.FORECAST),
        ("Có cảnh báo rủi ro gì không?", CopilotTool.ALERTS),
        ("Liệt kê nghĩa vụ đang nợ", CopilotTool.OBLIGATIONS),
        ("Giải thích quyết định này tại sao", CopilotTool.EXPLAIN),
        ("Xin chào", CopilotTool.CLARIFY),
    ],
)
def test_intent_routing(message, tool):
    assert parse_intent(message).tool == tool


def test_amount_and_months_parsed():
    intent = parse_intent("mua laptop 25 triệu trả góp 12 tháng")
    assert intent.amount == 25_000_000
    assert intent.months == 12


def test_amount_in_raw_digits():
    assert parse_intent("mua xe 30000000 tra gop").amount == 30_000_000
