from __future__ import annotations

from datetime import datetime, timezone
import logging

from app.modules.salary_offers.application.events import (
    AllManageesHaveProposal,
)
from app.modules.salary_offers.application.exporters import (
    build_salary_proposals_filename,
    build_salary_proposals_xlsx,
)
from app.modules.salary_offers.infrastructure.email_sender import (
    EmailAttachment,
    SalaryProposalEmailSender,
)
from app.modules.salary_offers.infrastructure.repo import SalaryOfferRepo


logger = logging.getLogger(__name__)
XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "spreadsheetml.sheet"
)


class SalaryOfferEventListener:
    def __init__(
        self,
        repo: SalaryOfferRepo,
        email_sender: SalaryProposalEmailSender,
    ) -> None:
        self.repo = repo
        self.email_sender = email_sender

    async def prepare_all_managees_have_proposal(
        self,
        *,
        audit_user: str,
        employee_id: int,
    ) -> AllManageesHaveProposal | None:
        app_manager = await self.repo.get_active_app_manager_by_audit_user(
            audit_user
        )
        if app_manager is None:
            return None

        year = datetime.now(timezone.utc).year
        managee_ids = await self.repo.get_active_managee_ids(
            app_manager.employee_id
        )
        if employee_id not in managee_ids:
            return None

        proposed_employee_ids = (
            await self.repo.get_salary_offer_employee_ids_for_year(
                employee_ids=managee_ids,
                year=year,
            )
        )

        if employee_id in proposed_employee_ids:
            return None

        missing_after_creation = (
            set(managee_ids) - set(proposed_employee_ids) - {employee_id}
        )
        if missing_after_creation:
            return None

        return AllManageesHaveProposal(app_manager=app_manager, year=year)

    async def handle_all_managees_have_proposal(
        self,
        event: AllManageesHaveProposal | None,
    ) -> None:
        if event is None:
            return

        rows = await self.repo.get_salary_proposal_export_rows(
            manager_employee_id=event.app_manager.employee_id,
            year=event.year,
        )
        workbook = build_salary_proposals_xlsx(rows)
        filename = build_salary_proposals_filename(
            event.app_manager.full_name,
            event.year,
        )

        attachment = EmailAttachment(
            filename=filename,
            content=workbook,
            content_type=XLSX_CONTENT_TYPE,
        )

        try:
            await self.email_sender.send_salary_proposals_completed(
                app_manager_name=event.app_manager.full_name,
                year=event.year,
                attachment=attachment,
            )
        except Exception:
            logger.exception(
                (
                    "Failed to send salary proposals completion "
                    "email for manager %s"
                ),
                event.app_manager.employee_id,
            )
