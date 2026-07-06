from __future__ import annotations

from typing import Any

from app.modules.assistant.application.ports import (
    AIProviderRequest,
    AIProviderResponse,
)
from app.modules.assistant.infrastructure.ai.base import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    def __init__(self) -> None:
        super().__init__(provider_name="mock")

    async def generate_response(
        self,
        request: AIProviderRequest,
    ) -> AIProviderResponse:
        used_tools = [tool.name for tool in request.tool_results]
        shap_tool = next(
            (
                tool
                for tool in request.tool_results
                if tool.name == "get_attrition_shap_drivers"
            ),
            None,
        )

        if shap_tool is None:
            return AIProviderResponse(
                answer=(
                    "No he podido recuperar contexto SHAP para esta consulta. "
                    "La respuesta sigue en modo POC sin IA generativa."
                ),
                used_tools=used_tools,
                provider=self.provider_name,
            )

        payload = shap_tool.payload
        if payload.get("status") != "ok":
            return AIProviderResponse(
                answer=payload.get(
                    "message",
                    "No hay valores SHAP disponibles para este empleado.",
                ),
                used_tools=used_tools,
                provider=self.provider_name,
            )

        return AIProviderResponse(
            answer=self._build_shap_driver_answer(payload),
            used_tools=used_tools,
            provider=self.provider_name,
        )

    def _build_shap_driver_answer(self, payload: dict[str, Any]) -> str:
        employee_id = payload.get("employee_id")
        model_version = payload.get("model_version")
        prediction_date = payload.get("prediction_date")
        attrition_rate = self._format_attrition_rate(payload.get("attrition_rate"))
        increasing = payload.get("drivers_increasing_risk") or []
        decreasing = payload.get("drivers_decreasing_risk") or []

        lines = [
            "POC sin IA generativa: estos son los factores SHAP principales "
            "de la prediccion original de riesgo de fuga.",
            "",
            f"Empleado: {employee_id}",
            f"Modelo: {model_version}",
            f"Fecha de prediccion: {prediction_date}",
        ]

        if attrition_rate is not None:
            lines.append(f"Riesgo de fuga actual registrado: {attrition_rate}")

        lines.extend(
            [
                "",
                "Factores que empujan hacia salida:",
                *self._format_driver_lines(increasing, empty="No hay drivers positivos relevantes."),
                "",
                "Factores que empujan hacia permanencia:",
                *self._format_driver_lines(decreasing, empty="No hay drivers protectores relevantes."),
                "",
                "Nota: SHAP explica como ha usado las variables el modelo; no demuestra causalidad por si mismo.",
            ]
        )
        return "\n".join(lines)

    def _format_driver_lines(
        self,
        drivers: list[dict[str, Any]],
        empty: str,
    ) -> list[str]:
        if not drivers:
            return [f"- {empty}"]

        lines = []
        for index, driver in enumerate(drivers[:3], start=1):
            label = driver.get("label") or driver.get("feature_key")
            shap_value = driver.get("shap_value")
            domain = driver.get("business_domain")
            domain_suffix = f" - {domain}" if domain else ""
            lines.append(
                f"{index}. {label}{domain_suffix}: SHAP {shap_value:+.4f}"
            )
        return lines

    def _format_attrition_rate(self, value: Any) -> str | None:
        if value is None:
            return None
        number = float(value)
        if number <= 1:
            number *= 100
        return f"{number:.1f}%"
