from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.utils import normalize_whatsapp
from app.services.dashboard_service import DashboardService
from app.services.navy_bf import calc_bf
from app.services.plan_service import PlanService, SHEET_MEDIDAS
from app.services.sheets_service import SheetsService

router = APIRouter()


class RegisterPayload(BaseModel):
    nome: str
    whatsapp_e164: str
    sexo: str
    altura_cm: float
    personal_id: str | None = "default"


class MeasurementPayload(BaseModel):
    whatsapp_e164: str
    data: str
    peso_kg: float
    cintura_cm: float
    pescoco_cm: float
    quadril_cm: float | None = None


class DashboardQuery(BaseModel):
    whatsapp_e164: str


@router.post("/api/register")
def register(payload: RegisterPayload) -> dict:
    sheets = SheetsService()
    plan = PlanService(sheets)
    plan.ensure_sheets()
    whatsapp = normalize_whatsapp(payload.whatsapp_e164)
    aluno = plan.create_or_get_aluno(
        nome=payload.nome,
        whatsapp_e164=whatsapp,
        sexo=payload.sexo,
        altura_cm=payload.altura_cm,
        personal_id=payload.personal_id or "default",
    )
    return {"status": "ok", "aluno": aluno}


@router.post("/api/measurements")
def measurements(payload: MeasurementPayload) -> dict:
    sheets = SheetsService()
    plan = PlanService(sheets)
    plan.ensure_sheets()
    whatsapp = normalize_whatsapp(payload.whatsapp_e164)
    aluno = plan.get_aluno_by_whatsapp(whatsapp)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    bf = calc_bf(
        aluno.get("sexo", ""),
        float(aluno.get("altura_cm") or 0),
        payload.cintura_cm,
        payload.pescoco_cm,
        payload.quadril_cm,
    )
    massa_magra = payload.peso_kg * (1 - bf / 100)
    plan._append_row(
        SHEET_MEDIDAS,
        {
            "aluno_id": aluno.get("aluno_id"),
            "data": payload.data,
            "peso_kg": payload.peso_kg,
            "cintura_cm": payload.cintura_cm,
            "pescoco_cm": payload.pescoco_cm,
            "quadril_cm": payload.quadril_cm or "",
            "bf_percent_auto": round(bf, 2),
            "massa_magra_estimada_auto": round(massa_magra, 2),
        },
    )
    return {"status": "ok", "bf_percent": bf, "massa_magra": massa_magra}


@router.get("/api/dashboard")
def dashboard(whatsapp_e164: str) -> dict:
    sheets = SheetsService()
    plan = PlanService(sheets)
    plan.ensure_sheets()
    whatsapp = normalize_whatsapp(whatsapp_e164)
    aluno = plan.get_aluno_by_whatsapp(whatsapp)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    dashboard_service = DashboardService(plan)
    data = dashboard_service.build_dashboard(aluno.get("aluno_id"))
    return {"status": "ok", "data": data}
