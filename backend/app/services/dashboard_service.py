from collections import Counter, defaultdict
from typing import Any

from app.core.utils import monday_start
from app.services.plan_service import (
    SHEET_LOGRESUMO,
    SHEET_LOGSETS,
    SHEET_MEDIDAS,
    PlanService,
)


class DashboardService:
    def __init__(self, plan_service: PlanService) -> None:
        self.plan_service = plan_service

    def _rows(self, sheet: str) -> list[dict[str, Any]]:
        return self.plan_service._rows_as_dicts(sheet)

    def build_dashboard(self, aluno_id: str) -> dict[str, Any]:
        medidas = [row for row in self._rows(SHEET_MEDIDAS) if row.get("aluno_id") == aluno_id]
        logresumo = [
            row for row in self._rows(SHEET_LOGRESUMO) if row.get("aluno_id") == aluno_id
        ]
        logsets = [row for row in self._rows(SHEET_LOGSETS) if row.get("aluno_id") == aluno_id]

        peso_series = [
            {"data": row.get("data"), "peso": float(row.get("peso_kg") or 0)}
            for row in medidas
            if row.get("peso_kg")
        ]
        bf_series = [
            {
                "data": row.get("data"),
                "bf": float(row.get("bf_percent_auto") or 0),
                "ffm": float(row.get("massa_magra_estimada_auto") or 0),
            }
            for row in medidas
            if row.get("bf_percent_auto")
        ]

        volume_semanal = defaultdict(float)
        volume_mensal = defaultdict(float)
        for row in logresumo:
            volume = float(row.get("volume_sessao_estimado") or 0)
            if not volume:
                continue
            semana = row.get("semana_inicio")
            mes = row.get("ano_mes")
            volume_semanal[semana] += volume
            volume_mensal[mes] += volume

        consistencia = Counter(
            row.get("semana_inicio")
            for row in logresumo
            if row.get("volume_sessao_estimado")
        )

        cargas_por_exercicio = defaultdict(list)
        for row in logsets:
            nome = row.get("exercicio_nome_canonico")
            if not nome:
                continue
            cargas_por_exercicio[nome].append(
                {
                    "data": row.get("data"),
                    "load": float(row.get("load_kg") or 0),
                }
            )

        exercise_counts = Counter(
            row.get("exercicio_nome_canonico")
            for row in logsets
            if row.get("exercicio_nome_canonico")
        )
        top_exercises = [name for name, _ in exercise_counts.most_common(5)]
        strength_index = defaultdict(float)
        for row in logsets:
            if row.get("exercicio_nome_canonico") not in top_exercises:
                continue
            data = row.get("data")
            if data:
                semana = monday_start(data)
                strength_index[semana] += float(row.get("load_kg") or 0)

        return {
            "peso": peso_series,
            "bf": bf_series,
            "volume_semanal": [
                {"semana": key, "volume": value}
                for key, value in sorted(volume_semanal.items())
            ],
            "volume_mensal": [
                {"mes": key, "volume": value}
                for key, value in sorted(volume_mensal.items())
            ],
            "consistencia": [
                {"semana": key, "treinos": value}
                for key, value in sorted(consistencia.items())
            ],
            "cargas": cargas_por_exercicio,
            "strength_index": [
                {"semana": key, "value": value}
                for key, value in sorted(strength_index.items())
            ],
            "exercicios_disponiveis": sorted(cargas_por_exercicio.keys()),
        }
