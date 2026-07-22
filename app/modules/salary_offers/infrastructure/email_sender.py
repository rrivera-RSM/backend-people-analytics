from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
import logging
from urllib.parse import quote

import httpx
import msal


logger = logging.getLogger(__name__)
GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]
GRAPH_USERS_URL = "https://graph.microsoft.com/v1.0/users"


@dataclass(frozen=True)
class EmailAttachment:
    filename: str
    content: bytes
    content_type: str


class SalaryProposalEmailSender:
    def __init__(
        self,
        *,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        sender_email: str,
        recipients: list[str],
    ) -> None:
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.sender_email = sender_email
        self.recipients = recipients
        self._confidential_client: (
            msal.ConfidentialClientApplication | None
        ) = None

    @property
    def is_configured(self) -> bool:
        return bool(
            self.tenant_id
            and self.client_id
            and self.client_secret
            and self.sender_email
            and self.recipients
        )

    async def send_salary_proposals_completed(
        self,
        *,
        app_manager_name: str,
        year: int,
        attachment: EmailAttachment,
    ) -> None:
        if not self.is_configured:
            logger.info(
                "Salary proposal notification skipped: "
                "Microsoft Graph mail is not configured"
            )
            return

        payload = self._build_payload(
            app_manager_name=app_manager_name,
            year=year,
            attachment=attachment,
        )
        access_token = await asyncio.to_thread(self._acquire_access_token)
        sender = quote(self.sender_email, safe="")
        url = f"{GRAPH_USERS_URL}/{sender}/sendMail"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code != httpx.codes.ACCEPTED:
            raise RuntimeError(
                "Microsoft Graph failed to send salary proposal email "
                f"(HTTP {response.status_code}): {response.text}"
            )

    def _acquire_access_token(self) -> str:
        if self._confidential_client is None:
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            self._confidential_client = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=authority,
            )

        result = self._confidential_client.acquire_token_for_client(
            scopes=GRAPH_SCOPE
        )
        access_token = result.get("access_token")
        if isinstance(access_token, str) and access_token:
            return access_token

        error = result.get("error", "unknown_error")
        description = result.get(
            "error_description",
            "Microsoft Entra ID did not return an access token",
        )
        raise RuntimeError(
            "Microsoft Graph app-only authentication failed: "
            f"{error} - {description}"
        )

    def _build_payload(
        self,
        *,
        app_manager_name: str,
        year: int,
        attachment: EmailAttachment,
    ) -> dict[str, object]:
        body = "\n".join(
            [
                "Hola,",
                "",
                (
                    "Todas las personas gestionadas por "
                    f"{app_manager_name} tienen propuesta salarial "
                    f"registrada para {year}."
                ),
                "",
                "Se adjunta el Excel con las propuestas salariales.",
                "",
                "People Analytics",
            ]
        )
        content_bytes = base64.b64encode(attachment.content).decode("ascii")

        return {
            "message": {
                "subject": (
                    "Salary proposals completed - "
                    f"{app_manager_name} - {year}"
                ),
                "body": {
                    "contentType": "Text",
                    "content": body,
                },
                "toRecipients": [
                    {"emailAddress": {"address": recipient}}
                    for recipient in self.recipients
                ],
                "attachments": [
                    {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": attachment.filename,
                        "contentType": attachment.content_type,
                        "contentBytes": content_bytes,
                    }
                ],
            },
            "saveToSentItems": True,
        }
