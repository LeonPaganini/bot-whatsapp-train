import logging

from app.core.logging import setup_logging
from app.services.plan_service import PlanService
from app.services.sheets_service import SheetsService


def main() -> None:
    setup_logging()
    logging.info("Configurando planilha MASTER")
    service = SheetsService()
    plan_service = PlanService(service)
    plan_service.ensure_sheets()
    logging.info("Planilha pronta")


if __name__ == "__main__":
    main()
