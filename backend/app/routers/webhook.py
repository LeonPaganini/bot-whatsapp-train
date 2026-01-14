import datetime as dt
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.core.utils import normalize_whatsapp
from app.services.parse_service import (
    match_exercise,
    parse_cargas_message,
    parse_plan_message,
)
from app.services.plan_service import PLAN_SEQUENCE, PlanService
from app.services.sheets_service import SheetsService
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()
LOGGER = logging.getLogger(__name__)


@router.get("/webhook/whatsapp")
def verify_webhook(request: Request) -> Any:
    hub_mode = request.query_params.get("hub.mode")
    hub_verify_token = request.query_params.get("hub.verify_token")
    hub_challenge = request.query_params.get("hub.challenge")
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge or 0)
    raise HTTPException(status_code=403, detail="Verificação falhou")


@router.post("/webhook/whatsapp")
async def webhook_whatsapp(request: Request) -> dict:
    payload = await request.json()
    LOGGER.info("Webhook payload: %s", payload)
    sheets = SheetsService()
    plan_service = PlanService(sheets)
    plan_service.ensure_sheets()
    whatsapp_service = WhatsAppService()

    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            for message in messages:
                if message.get("type") != "text":
                    continue
                text = message.get("text", {}).get("body", "")
                whatsapp = normalize_whatsapp(message.get("from", ""))
                aluno = plan_service.get_aluno_by_whatsapp(whatsapp)
                if not aluno:
                    plan_service.log_raw_message(
                        whatsapp, None, text, "texto", "erro", "Aluno não cadastrado"
                    )
                    whatsapp_service.send_text(
                        whatsapp,
                        "Aluno não cadastrado. Faça o cadastro em https://seu-site/cadastro.html",
                    )
                    continue
                aluno_id = aluno.get("aluno_id")
                texto_upper = text.strip().upper()
                if texto_upper.startswith("PLANO"):
                    try:
                        plan = parse_plan_message(text)
                        plan_service.save_plan(aluno_id, plan)
                        plan_service.log_raw_message(
                            whatsapp, aluno_id, text, "plano", "ok", None
                        )
                        whatsapp_service.send_text(whatsapp, "Plano atualizado com sucesso.")
                    except Exception as exc:  # noqa: BLE001
                        plan_service.log_raw_message(
                            whatsapp, aluno_id, text, "plano", "erro", str(exc)
                        )
                        whatsapp_service.send_text(
                            whatsapp,
                            f"Erro ao processar plano: {exc}",
                        )
                    continue

                if texto_upper.startswith("TREINO"):
                    sequence = plan_service.get_sequence_for_aluno(aluno_id)
                    next_index = int(aluno.get("next_workout_index") or 0)
                    sessao_nome = sequence[next_index % len(sequence)] if sequence else None
                    if not sessao_nome:
                        whatsapp_service.send_text(whatsapp, "Plano não encontrado.")
                        continue
                    exercises = plan_service.get_plan_for_session(aluno_id, sessao_nome)
                    if not exercises:
                        whatsapp_service.send_text(
                            whatsapp, "Sessão sem exercícios. Envie PLANO primeiro."
                        )
                        continue
                    data = dt.date.today().isoformat()
                    session_id = plan_service.create_session_draft(
                        aluno_id, sessao_nome, next_index, data
                    )
                    linhas = [f"Treino {sessao_nome}", f"Sessão ID: {session_id}"]
                    for ex in exercises:
                        linhas.append(
                            f"- {ex.exercicio_nome_canonico} | {ex.sets}x{ex.reps_alvo}"
                        )
                    whatsapp_service.send_text(whatsapp, "\n".join(linhas))
                    plan_service.log_raw_message(
                        whatsapp, aluno_id, text, "treino", "ok", None
                    )
                    continue

                if texto_upper.startswith("CARGAS") or ":" in text:
                    try:
                        parsed = parse_cargas_message(text)
                        active = plan_service.get_active_session(aluno_id)
                        if not active:
                            whatsapp_service.send_text(
                                whatsapp,
                                "Nenhuma sessão ativa. Envie TREINO para iniciar.",
                            )
                            plan_service.log_raw_message(
                                whatsapp,
                                aluno_id,
                                text,
                                "cargas",
                                "erro",
                                "Sessão ativa não encontrada",
                            )
                            continue
                        sessao_nome = active.get("sessao_nome", "")
                        session_id = active.get("session_instance_id")
                        sequence_index = int(active.get("sequence_index_usado") or 0)
                        exercises = plan_service.get_plan_for_session(aluno_id, sessao_nome)
                        total_volume = 0.0
                        for item in parsed.items:
                            match = match_exercise(item.exercicio_nome, exercises)
                            if not match:
                                whatsapp_service.send_text(
                                    whatsapp,
                                    "Exercício não reconhecido. Use o nome canônico do treino.",
                                )
                                raise ValueError("Exercício não reconhecido")
                            total_volume += plan_service.log_sets(
                                aluno_id,
                                session_id,
                                active.get("data", ""),
                                sessao_nome,
                                match,
                                item.loads,
                            )
                        plan_service.update_session_summary(session_id, total_volume, None)
                        plan_service.update_next_workout_index(
                            aluno_id, (sequence_index + 1) % len(PLAN_SEQUENCE)
                        )
                        plan_service.log_raw_message(
                            whatsapp, aluno_id, text, "cargas", "ok", None
                        )
                        whatsapp_service.send_text(whatsapp, "Cargas registradas!")
                    except Exception as exc:  # noqa: BLE001
                        plan_service.log_raw_message(
                            whatsapp, aluno_id, text, "cargas", "erro", str(exc)
                        )
                    continue

                whatsapp_service.send_text(
                    whatsapp,
                    "Comando não reconhecido. Use TREINO, PLANO ou CARGAS.",
                )
                plan_service.log_raw_message(
                    whatsapp, aluno_id, text, "texto", "erro", "Comando inválido"
                )

    return {"status": "ok"}
