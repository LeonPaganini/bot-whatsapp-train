import logging
import uuid
from typing import Any

from app.core.utils import monday_start, now_iso, year_month
from app.services.parse_service import ParsedPlan, PlanExercise
from app.services.sheets_service import SheetsService

LOGGER = logging.getLogger(__name__)

SHEET_PERSONALS = "Personals"
SHEET_ALUNOS = "Alunos"
SHEET_PLAN_SEQUENCE = "PlanSequence"
SHEET_PLANO = "Plano"
SHEET_LOGSETS = "LogSets"
SHEET_LOGRESUMO = "LogResumo"
SHEET_MEDIDAS = "Medidas"
SHEET_RAW = "RawMessages"

PLAN_SEQUENCE = ["PUSH", "PULL", "LEGS 1", "UPPER", "LEGS 2"]

SHEET_HEADERS = {
    SHEET_PERSONALS: [
        "personal_id",
        "nome",
        "whatsapp_e164",
        "created_at",
    ],
    SHEET_ALUNOS: [
        "aluno_id",
        "personal_id",
        "nome",
        "whatsapp_e164",
        "sexo",
        "altura_cm",
        "created_at",
        "ativo",
        "next_workout_index",
    ],
    SHEET_PLAN_SEQUENCE: [
        "aluno_id",
        "index",
        "sessao_nome",
    ],
    SHEET_PLANO: [
        "aluno_id",
        "sessao_nome",
        "exercicio_id",
        "exercicio_nome_canonico",
        "sets",
        "reps_alvo",
        "aliases",
    ],
    SHEET_LOGSETS: [
        "aluno_id",
        "session_instance_id",
        "data",
        "sessao_nome",
        "exercicio_id",
        "exercicio_nome_canonico",
        "set_index",
        "load_kg",
    ],
    SHEET_LOGRESUMO: [
        "aluno_id",
        "session_instance_id",
        "data",
        "sessao_nome",
        "sequence_index_usado",
        "peso_kg",
        "volume_sessao_estimado",
        "semana_inicio",
        "ano_mes",
    ],
    SHEET_MEDIDAS: [
        "aluno_id",
        "data",
        "peso_kg",
        "cintura_cm",
        "pescoco_cm",
        "quadril_cm",
        "bf_percent_auto",
        "massa_magra_estimada_auto",
    ],
    SHEET_RAW: [
        "ts",
        "whatsapp_e164",
        "aluno_id",
        "texto_original",
        "tipo",
        "status_parse",
        "erro",
    ],
}


class PlanService:
    def __init__(self, sheets: SheetsService) -> None:
        self.sheets = sheets

    def ensure_sheets(self) -> None:
        for name, headers in SHEET_HEADERS.items():
            self.sheets.ensure_sheet(name, headers)

    def _rows_as_dicts(self, sheet_name: str) -> list[dict[str, Any]]:
        values = self.sheets.get_values(sheet_name)
        if not values:
            return []
        headers = values[0]
        rows = []
        for row in values[1:]:
            data = {headers[idx]: row[idx] if idx < len(row) else "" for idx in range(len(headers))}
            rows.append(data)
        return rows

    def _append_row(self, sheet_name: str, data: dict[str, Any]) -> None:
        headers = SHEET_HEADERS[sheet_name]
        row = [data.get(header, "") for header in headers]
        self.sheets.append_rows(sheet_name, [row])

    def get_aluno_by_whatsapp(self, whatsapp_e164: str) -> dict[str, Any] | None:
        rows = self._rows_as_dicts(SHEET_ALUNOS)
        for row in rows:
            if row.get("whatsapp_e164") == whatsapp_e164:
                return row
        return None

    def create_or_get_aluno(
        self,
        nome: str,
        whatsapp_e164: str,
        sexo: str,
        altura_cm: float,
        personal_id: str,
    ) -> dict[str, Any]:
        existing = self.get_aluno_by_whatsapp(whatsapp_e164)
        if existing:
            return existing
        aluno_id = str(uuid.uuid4())
        self._append_row(
            SHEET_ALUNOS,
            {
                "aluno_id": aluno_id,
                "personal_id": personal_id,
                "nome": nome,
                "whatsapp_e164": whatsapp_e164,
                "sexo": sexo,
                "altura_cm": altura_cm,
                "created_at": now_iso(),
                "ativo": "1",
                "next_workout_index": "0",
            },
        )
        for idx, sessao in enumerate(PLAN_SEQUENCE):
            self._append_row(
                SHEET_PLAN_SEQUENCE,
                {"aluno_id": aluno_id, "index": str(idx), "sessao_nome": sessao},
            )
        return self.get_aluno_by_whatsapp(whatsapp_e164) or {}

    def update_next_workout_index(self, aluno_id: str, next_index: int) -> None:
        values = self.sheets.get_values(SHEET_ALUNOS)
        if not values:
            return
        headers = values[0]
        target_row = None
        target_row_values = None
        for row_index, row in enumerate(values[1:], start=2):
            if len(row) > 0 and row[0] == aluno_id:
                target_row = row_index
                target_row_values = row
                break
        if not target_row or target_row_values is None:
            return
        row_data = {
            headers[i]: target_row_values[i] if i < len(target_row_values) else ""
            for i in range(len(headers))
        }
        row_data["next_workout_index"] = str(next_index)
        updated = [row_data.get(header, "") for header in headers]
        self.sheets.update_row(SHEET_ALUNOS, target_row, updated)

    def save_plan(self, aluno_id: str, plan: ParsedPlan) -> None:
        values = self.sheets.get_values(SHEET_PLANO)
        headers = values[0] if values else SHEET_HEADERS[SHEET_PLANO]
        rows = [headers]
        if values:
            for row in values[1:]:
                if len(row) > 0 and row[0] == aluno_id:
                    continue
                rows.append(row)
        for exercise in plan.exercises:
            rows.append(
                [
                    aluno_id,
                    exercise.sessao_nome,
                    exercise.exercicio_id,
                    exercise.exercicio_nome_canonico,
                    str(exercise.sets),
                    str(exercise.reps_alvo),
                    ",".join(exercise.aliases),
                ]
            )
        self.sheets.replace_rows(SHEET_PLANO, rows)

    def get_plan_for_session(self, aluno_id: str, sessao_nome: str) -> list[PlanExercise]:
        rows = self._rows_as_dicts(SHEET_PLANO)
        exercises = []
        for row in rows:
            if row.get("aluno_id") == aluno_id and row.get("sessao_nome") == sessao_nome:
                aliases = [alias.strip() for alias in row.get("aliases", "").split(",") if alias]
                exercises.append(
                    PlanExercise(
                        sessao_nome=row.get("sessao_nome", ""),
                        exercicio_id=row.get("exercicio_id", ""),
                        exercicio_nome_canonico=row.get("exercicio_nome_canonico", ""),
                        sets=int(float(row.get("sets", 0) or 0)),
                        reps_alvo=int(float(row.get("reps_alvo", 0) or 0)),
                        aliases=aliases,
                    )
                )
        return exercises

    def get_sequence_for_aluno(self, aluno_id: str) -> list[str]:
        rows = self._rows_as_dicts(SHEET_PLAN_SEQUENCE)
        sequence = [row for row in rows if row.get("aluno_id") == aluno_id]
        sequence.sort(key=lambda item: int(item.get("index", 0)))
        return [row.get("sessao_nome", "") for row in sequence]

    def create_session_draft(
        self, aluno_id: str, sessao_nome: str, sequence_index: int, data: str
    ) -> str:
        session_instance_id = str(uuid.uuid4())
        self._append_row(
            SHEET_LOGRESUMO,
            {
                "aluno_id": aluno_id,
                "session_instance_id": session_instance_id,
                "data": data,
                "sessao_nome": sessao_nome,
                "sequence_index_usado": str(sequence_index),
                "peso_kg": "",
                "volume_sessao_estimado": "",
                "semana_inicio": monday_start(data),
                "ano_mes": year_month(data),
            },
        )
        return session_instance_id

    def get_active_session(self, aluno_id: str) -> dict[str, Any] | None:
        rows = self._rows_as_dicts(SHEET_LOGRESUMO)
        for row in reversed(rows):
            if row.get("aluno_id") == aluno_id and not row.get("volume_sessao_estimado"):
                return row
        return None

    def update_session_summary(
        self, session_instance_id: str, volume: float, peso_kg: str | None
    ) -> None:
        values = self.sheets.get_values(SHEET_LOGRESUMO)
        if not values:
            return
        headers = values[0]
        target_row = None
        row_data = None
        for row_index, row in enumerate(values[1:], start=2):
            if len(row) > 1 and row[1] == session_instance_id:
                target_row = row_index
                row_data = row
                break
        if not target_row or row_data is None:
            return
        data = {headers[i]: row_data[i] if i < len(row_data) else "" for i in range(len(headers))}
        data["volume_sessao_estimado"] = str(volume)
        if peso_kg:
            data["peso_kg"] = peso_kg
        updated = [data.get(header, "") for header in headers]
        self.sheets.update_row(SHEET_LOGRESUMO, target_row, updated)

    def log_sets(
        self,
        aluno_id: str,
        session_instance_id: str,
        data: str,
        sessao_nome: str,
        exercicio: PlanExercise,
        loads: list[float],
    ) -> float:
        volume = 0.0
        rows = []
        for idx, load in enumerate(loads, start=1):
            rows.append(
                [
                    aluno_id,
                    session_instance_id,
                    data,
                    sessao_nome,
                    exercicio.exercicio_id,
                    exercicio.exercicio_nome_canonico,
                    str(idx),
                    str(load),
                ]
            )
            volume += load * exercicio.reps_alvo
        self.sheets.append_rows(SHEET_LOGSETS, rows)
        return volume

    def log_raw_message(
        self,
        whatsapp_e164: str,
        aluno_id: str | None,
        texto_original: str,
        tipo: str,
        status_parse: str,
        erro: str | None,
    ) -> None:
        self._append_row(
            SHEET_RAW,
            {
                "ts": now_iso(),
                "whatsapp_e164": whatsapp_e164,
                "aluno_id": aluno_id or "",
                "texto_original": texto_original,
                "tipo": tipo,
                "status_parse": status_parse,
                "erro": erro or "",
            },
        )
