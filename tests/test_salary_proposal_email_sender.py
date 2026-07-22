import base64
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx

from app.modules.salary_offers.infrastructure.email_sender import (
    EmailAttachment,
    SalaryProposalEmailSender,
)


MODULE = "app.modules.salary_offers.infrastructure.email_sender"


def build_sender(**overrides: object) -> SalaryProposalEmailSender:
    values: dict[str, object] = {
        "tenant_id": "tenant-id",
        "client_id": "client-id",
        "client_secret": "client-secret",
        "sender_email": "people+analytics@rsm.es",
        "recipients": ["rrivera@rsm.es"],
    }
    values.update(overrides)
    return SalaryProposalEmailSender(**values)


def build_async_client(response: Mock) -> tuple[MagicMock, AsyncMock]:
    client = AsyncMock()
    client.post.return_value = response

    context_manager = MagicMock()
    context_manager.__aenter__ = AsyncMock(return_value=client)
    context_manager.__aexit__ = AsyncMock(return_value=False)
    return context_manager, client


class SalaryProposalEmailSenderTests(IsolatedAsyncioTestCase):
    async def test_sends_graph_payload_with_attachment(self) -> None:
        sender = build_sender()
        sender._acquire_access_token = Mock(return_value="graph-token")
        context_manager, client = build_async_client(
            Mock(status_code=httpx.codes.ACCEPTED, text="")
        )
        attachment = EmailAttachment(
            filename="propuestas.xlsx",
            content=b"xlsx-content",
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        with patch(
            f"{MODULE}.httpx.AsyncClient",
            return_value=context_manager,
        ):
            await sender.send_salary_proposals_completed(
                app_manager_name="Ana Manager",
                year=2026,
                attachment=attachment,
            )

        client.post.assert_awaited_once()
        request = client.post.await_args
        self.assertEqual(
            request.args[0],
            (
                "https://graph.microsoft.com/v1.0/users/"
                "people%2Banalytics%40rsm.es/sendMail"
            ),
        )
        self.assertEqual(
            request.kwargs["headers"]["Authorization"],
            "Bearer graph-token",
        )

        payload = request.kwargs["json"]
        message = payload["message"]
        self.assertEqual(
            message["toRecipients"],
            [{"emailAddress": {"address": "rrivera@rsm.es"}}],
        )
        self.assertEqual(
            message["attachments"][0]["contentBytes"],
            base64.b64encode(b"xlsx-content").decode("ascii"),
        )
        self.assertTrue(payload["saveToSentItems"])

    async def test_skips_send_when_graph_is_not_configured(self) -> None:
        sender = build_sender(client_secret="")
        acquire_access_token = Mock()
        sender._acquire_access_token = acquire_access_token

        with patch(f"{MODULE}.httpx.AsyncClient") as async_client:
            await sender.send_salary_proposals_completed(
                app_manager_name="Ana Manager",
                year=2026,
                attachment=EmailAttachment(
                    filename="propuestas.xlsx",
                    content=b"xlsx-content",
                    content_type="application/octet-stream",
                ),
            )

        acquire_access_token.assert_not_called()
        async_client.assert_not_called()

    async def test_raises_when_graph_rejects_send(self) -> None:
        sender = build_sender()
        sender._acquire_access_token = Mock(return_value="graph-token")
        context_manager, _ = build_async_client(
            Mock(status_code=httpx.codes.FORBIDDEN, text="Access denied")
        )

        with (
            patch(
                f"{MODULE}.httpx.AsyncClient",
                return_value=context_manager,
            ),
            self.assertRaisesRegex(RuntimeError, "HTTP 403"),
        ):
            await sender.send_salary_proposals_completed(
                app_manager_name="Ana Manager",
                year=2026,
                attachment=EmailAttachment(
                    filename="propuestas.xlsx",
                    content=b"xlsx-content",
                    content_type="application/octet-stream",
                ),
            )

    def test_raises_when_entra_does_not_return_token(self) -> None:
        sender = build_sender()
        confidential_client = Mock()
        confidential_client.acquire_token_for_client.return_value = {
            "error": "invalid_client",
            "error_description": "Secret expired",
        }
        sender._confidential_client = confidential_client

        with self.assertRaisesRegex(RuntimeError, "invalid_client"):
            sender._acquire_access_token()
