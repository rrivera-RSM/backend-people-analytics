from __future__ import annotations

from app.modules.assistant.application.ports import AIToolResult
from app.modules.assistant.infrastructure.repo import AssistantShapRepository


class AssistantToolRegistry:
    def __init__(self, shap_repository: AssistantShapRepository) -> None:
        self.shap_repository = shap_repository

    async def build_context(self, employee_id: int) -> list[AIToolResult]:
        shap_context = await self.shap_repository.get_employee_attrition_shap_context(
            employee_id=employee_id,
        )

        if shap_context is None:
            return [
                AIToolResult(
                    name="get_attrition_shap_drivers",
                    payload={
                        "employee_id": employee_id,
                        "status": "not_found",
                        "message": (
                            "No hay valores SHAP disponibles para la prediccion "
                            "original de fuga de este empleado."
                        ),
                    },
                )
            ]

        return [
            AIToolResult(
                name="get_attrition_shap_drivers",
                payload={"status": "ok", **shap_context},
            )
        ]
