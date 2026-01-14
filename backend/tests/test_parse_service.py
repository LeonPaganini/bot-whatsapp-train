from app.services.parse_service import parse_cargas_message, parse_plan_message


def test_parse_plan_message():
    message = """PLANO
PUSH
Supino inclinado|4|8|sup inclinado
PULL
Remada|3|10|
"""
    parsed = parse_plan_message(message)
    assert len(parsed.exercises) == 2
    assert parsed.exercises[0].sessao_nome == "PUSH"
    assert parsed.exercises[0].sets == 4
    assert parsed.exercises[1].sessao_nome == "PULL"


def test_parse_cargas_message():
    message = """CARGAS
Supino inclinado: 90/85/80
"""
    parsed = parse_cargas_message(message)
    assert len(parsed.items) == 1
    assert parsed.items[0].loads == [90.0, 85.0, 80.0]


def test_parse_cargas_message_without_prefix():
    message = "Supino inclinado: 90,85,80"
    parsed = parse_cargas_message(message)
    assert parsed.items[0].loads == [90.0, 85.0, 80.0]
