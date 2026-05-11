from __future__ import annotations

from dataclasses import dataclass

from app.modules.evaluations.infrastructure.repo import (
    EvaluationScatterRepository,
)
from app.modules.evaluations.schemas import (
    EvaluationScatterLatestCycleOut,
)


class EvaluationScatterNotFoundError(Exception):
    """Error de dominio para casos donde no hay datos de evaluaciones."""

    pass


@dataclass(frozen=True, slots=True)
class EvaluationScatterRules:
    """
    Reglas de negocio del scatter de evaluaciones.

    De momento no necesitamos thresholds complejos aquí, pero dejamos la
    estructura preparada por si más adelante quieres:
    - limitar por score mínimo
    - excluir categorías
    - filtrar solo empleados activos en fecha distinta
    """

    require_points: bool = False


class EvaluationScatterService:
    def __init__(
        self,
        repo: EvaluationScatterRepository,
        rules: EvaluationScatterRules | None = None,
    ) -> None:
        self.repo = repo
        self.rules = rules or EvaluationScatterRules()

    async def get_latest_cycle_scatter(
        self,
    ) -> EvaluationScatterLatestCycleOut:
        """
        Devuelve el scatter anónimo del último ejercicio disponible.

        El dataset está pensado para frontend:
        - una sola llamada
        - una fila por empleado
        - sin PII
        - reutilizable al cambiar de empleado seleccionado
        """
        result = await self.repo.get_latest_cycle_scatter()

        if self.rules.require_points and result.total_points == 0:
            raise EvaluationScatterNotFoundError(
                "No hay datos de evaluaciones para el último ejercicio."
            )

        return result
