from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.modules.employee_insights.infrastructure.repo import (
    EmployeeInsightRepository,
)
from app.modules.employee_insights.schemas import (
    EmployeeInsightContext,
    EmployeeInsightFeaturesOut,
    EmployeeInsightItemOut,
    EmployeeInsightsResponseOut,
    InsightCode,
    InsightFamily,
)


class EmployeeNotFoundError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class EmployeeInsightRules:
    # --- PERFORMANCE ---
    high_performance_score: float = 90.0
    medium_performance_score: float = 70.0
    performance_delta_threshold: float = 5.0

    # --- ONA ACTIVO refinado ---
    high_ona_percentile: float = 80.0

    # --- ONA RELACIONES (people.ona_insights) ---
    strong_transversal_leadership_threshold: float = 3.0
    transversal_influence_threshold: float = 2.0
    lateral_influence_threshold: float = 2.0
    upward_influence_threshold: float = 2.0
    bridge_person_threshold: float = 3.0


class EmployeeInsightService:
    def __init__(
        self,
        repo: EmployeeInsightRepository,
        rules: EmployeeInsightRules | None = None,
    ) -> None:
        self.repo = repo
        self.rules = rules or EmployeeInsightRules()

    async def get_employee_insights(
        self,
        employee_id: int,
        as_of: datetime | None = None,
    ) -> EmployeeInsightsResponseOut:
        as_of = as_of or datetime.now(timezone.utc)

        context = await self.repo.get_employee_insight_context(
            as_of=as_of,
            employee_id=employee_id,
        )
        if context is None:
            raise EmployeeNotFoundError(
                f"No existe el empleado con id={employee_id}"
            )

        warnings: list[str] = []

        features = self._build_features(context=context, as_of=as_of)

        insights: list[EmployeeInsightItemOut] = []
        insights.extend(
            self._build_performance_insights(
                context=context,
                features=features,
            )
        )
        insights.extend(
            self._build_ona_relationship_insights(
                context=context,
                features=features,
            )
        )
        insights.extend(
            self._build_ona_active_insights(
                context=context,
                features=features,
            )
        )
        insights.extend(
            self._build_ona_and_performance_insights(
                context=context,
                features=features,
            )
        )

        if not context.current_evaluation:
            warnings.append(
                "No hay evaluaciones disponibles para el empleado; "
                "los insights de desempeño no se han podido calcular."
            )

        if not context.ona_records:
            warnings.append(
                "No hay registros ONA activos para el empleado; "
                "los insights de ONA activo no se han podido calcular."
            )

        if not context.ona_insight_records:
            warnings.append(
                "No hay registros en people.ona_insights para el empleado; "
                "los insights ONA relacionales no se han podido calcular."
            )
        elif len(context.ona_insight_records) > 1:
            warnings.append(
                "En esta v2, múltiples registros de people.ona_insights se "
                "agregan por máximos de métrica. Si necesitas granularidad "
                "por ona_category, conviene exponer un detalle adicional."
            )

        insights = sorted(insights, key=lambda item: item.priority)

        first_name = context.employee.first_name or ""
        last_name = context.employee.last_name or ""
        full_name = f"{first_name} {last_name}".strip()

        return EmployeeInsightsResponseOut(
            generated_at=datetime.now(timezone.utc),
            as_of=as_of,
            employee_id=context.employee.id,
            employee_full_name=full_name,
            features=features,
            insights=insights,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Feature builders
    # ------------------------------------------------------------------

    def _build_features(
        self,
        context: EmployeeInsightContext,
        as_of: datetime,
    ) -> EmployeeInsightFeaturesOut:
        current_score_raw = (
            context.current_evaluation.final_score
            if context.current_evaluation
            else None
        )
        previous_score_raw = (
            context.previous_evaluation.final_score
            if context.previous_evaluation
            else None
        )

        current_score_normalized = self._normalize_performance_score(
            current_score_raw
        )
        previous_score_normalized = self._normalize_performance_score(
            previous_score_raw
        )

        performance_delta_normalized = None
        if (
            current_score_normalized is not None
            and previous_score_normalized is not None
        ):
            performance_delta_normalized = round(
                current_score_normalized - previous_score_normalized,
                2,
            )

        performance_band = self._get_performance_band(
            current_score_normalized
        )
        performance_trend = self._get_performance_trend(
            performance_delta_normalized
        )

        ona_aggregates = self._aggregate_ona_records(context.ona_records)
        ona_insight_aggregates = self._aggregate_ona_insight_records(
            context.ona_insight_records
        )

        employee_active = (
            context.employee.left_at is None
            or context.employee.left_at > as_of
        )
        category = getattr(context.employee, "category_name", None)

        return EmployeeInsightFeaturesOut(
            employee_active=employee_active,
            current_evaluation_at=(
                context.current_evaluation.evaluation_at
                if context.current_evaluation
                else None
            ),
            previous_evaluation_at=(
                context.previous_evaluation.evaluation_at
                if context.previous_evaluation
                else None
            ),
            category=category,
            current_evaluation_score_raw=current_score_raw,
            previous_evaluation_score_raw=previous_score_raw,
            current_evaluation_score_normalized=current_score_normalized,
            previous_evaluation_score_normalized=previous_score_normalized,
            performance_delta_normalized=performance_delta_normalized,
            performance_band=performance_band,
            performance_trend=performance_trend,
            ona_record_count=ona_aggregates["ona_record_count"],
            ona_category_ids=ona_aggregates["ona_category_ids"],
            ona_influence_ids=ona_aggregates["ona_influence_ids"],
            ona_percentile_1=ona_aggregates["ona_percentile_1"],
            ona_percentile_2=ona_aggregates["ona_percentile_2"],
            ona_percentile_3=ona_aggregates["ona_percentile_3"],
            ona_percentile_4=ona_aggregates["ona_percentile_4"],
            ona_primary_category=ona_insight_aggregates[
                "ona_primary_category"
            ],
            degree_centrality=ona_aggregates["degree_centrality"],
            closeness_centrality=ona_aggregates["closeness_centrality"],
            betweenness_centrality=ona_aggregates["betweenness_centrality"],
            eigenvector_centrality=ona_aggregates["eigenvector_centrality"],
            ona_insight_record_count=ona_insight_aggregates[
                "ona_insight_record_count"
            ],
            ona_insight_categories=ona_insight_aggregates[
                "ona_insight_categories"
            ],
            n_different_categories_in=ona_insight_aggregates[
                "n_different_categories_in"
            ],
            n_same_category_in=ona_insight_aggregates["n_same_category_in"],
            n_upper_categories_in=ona_insight_aggregates[
                "n_upper_categories_in"
            ],
            n_different_departments_in=ona_insight_aggregates[
                "n_different_departments_in"
            ],
            n_total_votes_in=ona_insight_aggregates["n_total_votes_in"],
            percentile_80_votes_dpt_office=ona_insight_aggregates[
                "percentile_80_votes_dpt_office"
            ],
            incoming_unique_relations=context.incoming_unique_relations,
            outgoing_unique_relations=context.outgoing_unique_relations,
            unique_relations=context.unique_relations,
            influence=ona_insight_aggregates["influence"],
            n_lower_categories_in=ona_insight_aggregates[
                "n_lower_categories_in"
            ],
            p80_n_different_categories_in=ona_insight_aggregates[
                "p80_n_different_categories_in"
            ],
            p80_n_different_departments_in=ona_insight_aggregates[
                "p80_n_different_departments_in"
            ],
            n_respuestas=ona_insight_aggregates["n_respuestas"],
            tasa_respuestas=ona_insight_aggregates["tasa_respuestas"],
            n_same_dept_office_in_no_ci=ona_insight_aggregates[
                "n_same_dept_office_in_no_ci"
            ],
            p80_n_same_dept_office_in_no_ci=ona_insight_aggregates[
                "p80_n_same_dept_office_in_no_ci"
            ],
        )

    def _aggregate_ona_records(self, records: list[Any]) -> dict[str, Any]:
        if not records:
            return {
                "ona_record_count": 0,
                "ona_category_ids": [],
                "ona_influence_ids": [],
                "ona_percentile_1": None,
                "ona_percentile_2": None,
                "ona_percentile_3": None,
                "ona_percentile_4": None,
                "degree_centrality": None,
                "closeness_centrality": None,
                "betweenness_centrality": None,
                "eigenvector_centrality": None,
            }

        def max_normalized_percentile(
            values: list[float | None],
        ) -> float | None:
            normalized = [
                self._normalize_percentile(v) for v in values if v is not None
            ]
            return round(max(normalized), 2) if normalized else None

        def max_nullable(values: list[float | None]) -> float | None:
            not_none = [v for v in values if v is not None]
            return round(max(not_none), 4) if not_none else None

        return {
            "ona_record_count": len(records),
            "ona_category_ids": sorted(
                {record.ona_category_id for record in records}
            ),
            "ona_influence_ids": sorted(
                {record.ona_influence_id for record in records}
            ),
            "ona_percentile_1": max_normalized_percentile(
                [record.percentile_1 for record in records]
            ),
            "ona_percentile_2": max_normalized_percentile(
                [record.percentile_2 for record in records]
            ),
            "ona_percentile_3": max_normalized_percentile(
                [record.percentile_3 for record in records]
            ),
            "ona_percentile_4": max_normalized_percentile(
                [record.percentile_4 for record in records]
            ),
            "degree_centrality": max_nullable(
                [record.degree_centrality for record in records]
            ),
            "closeness_centrality": max_nullable(
                [record.closeness_centrality for record in records]
            ),
            "betweenness_centrality": max_nullable(
                [record.betweenness_centrality for record in records]
            ),
            "eigenvector_centrality": max_nullable(
                [record.eigenvector_centrality for record in records]
            ),
        }

    def _aggregate_ona_insight_records(
        self,
        records: list[Any],
    ) -> dict[str, Any]:
        """
        Agrega registros de people.ona_insights.
        En v2: cuando hay múltiples registros, se agregan por máximos (criterio conservador).
        - Métricas del empleado: max
        - Percentiles/umbrales de referencia (p80_*): max (evita falsos positivos)
        """

        # Base “vacía” con TODOS los campos que el service/insights pueden consumir
        empty = {
            "ona_insight_record_count": 0,
            "ona_insight_categories": [],
            "ona_primary_category": None,
            # gating / clasificación
            "influence": None,
            # core metrics
            "n_different_categories_in": None,
            "n_same_category_in": None,
            "n_upper_categories_in": None,
            "n_lower_categories_in": None,
            "n_different_departments_in": None,
            # calidad / participación
            "n_respuestas": None,
            "tasa_respuestas": None,
            # referencia equipo (dept-office)
            "n_same_dept_office_in_no_ci": None,
            "p80_n_same_dept_office_in_no_ci": None,
            # referencia percentiles globales
            "p80_n_different_categories_in": None,
            "p80_n_different_departments_in": None,
            # legacy (si aún lo necesitas en otros lados)
            "n_total_votes_in": None,
            "percentile_80_votes_dpt_office": None,
        }

        if not records:
            return empty

        # Prioridad para escoger “categoría principal” (lo más fuerte primero)
        category_priority = {
            "central": 1,
            "hipo": 2,
            "intermediary": 3,
            "peripheral": 4,
        }

        # ------------- helpers -------------
        def _get(record: Any, field: str) -> Any:
            # Evita reventar si algún campo todavía no existe en el modelo/SQL
            return getattr(record, field, None)

        def max_decimal_field(field: str) -> float | None:
            values: list[float] = []
            for r in records:
                v = _get(r, field)
                if v is None:
                    continue
                # Decimal / int / float -> float
                try:
                    values.append(float(v))
                except (TypeError, ValueError):
                    continue
            return round(max(values), 2) if values else None

        def max_float_field(field: str, ndigits: int = 2) -> float | None:
            values: list[float] = []
            for r in records:
                v = _get(r, field)
                if v is None:
                    continue
                try:
                    values.append(float(v))
                except (TypeError, ValueError):
                    continue
            return round(max(values), ndigits) if values else None

        # ------------- categorías -------------
        categories = sorted(
            {
                (_get(r, "ona_category") or "").strip()
                for r in records
                if _get(r, "ona_category")
            }
        )

        primary_category = (
            min(categories, key=lambda c: category_priority.get(c, 999))
            if categories
            else None
        )

        # “influence”:
        # - ideal: un campo explícito record.influence
        # - fallback: usar la categoría principal (central/hipo/...)
        influence_values = sorted(
            {
                (_get(r, "influence") or "").strip()
                for r in records
                if _get(r, "influence")
            }
        )
        influence = (
            min(influence_values, key=lambda c: category_priority.get(c, 999))
            if influence_values
            else primary_category
        )

        # ------------- agregación -------------
        aggregated = {
            "ona_insight_record_count": len(records),
            "ona_insight_categories": categories,
            "ona_primary_category": primary_category,
            "influence": influence,
            # core metrics (max)
            "n_different_categories_in": max_decimal_field(
                "n_different_categories_in"
            ),
            "n_same_category_in": max_decimal_field("n_same_category_in"),
            "n_upper_categories_in": max_decimal_field(
                "n_upper_categories_in"
            ),
            "n_lower_categories_in": max_decimal_field(
                "n_lower_categories_in"
            ),
            "n_different_departments_in": max_decimal_field(
                "n_different_departments_in"
            ),
            # calidad / participación (max; si tasa es 0..1 la dejamos tal cual, no normalizamos aquí)
            "n_respuestas": max_decimal_field("n_respuestas"),
            "tasa_respuestas": max_float_field("tasa_respuestas", ndigits=4),
            # equipo dept-office
            "n_same_dept_office_in_no_ci": max_decimal_field(
                "n_same_dept_office_in_no_ci"
            ),
            "p80_n_same_dept_office_in_no_ci": max_decimal_field(
                "p80_n_same_dept_office_in_no_ci"
            ),
            # percentiles de referencia (conservador: max)
            "p80_n_different_categories_in": max_decimal_field(
                "p80_n_different_categories_in"
            ),
            "p80_n_different_departments_in": max_decimal_field(
                "p80_n_different_departments_in"
            ),
            # legacy
            "n_total_votes_in": max_decimal_field("n_total_votes_in"),
            "percentile_80_votes_dpt_office": max_decimal_field(
                "percentile_80_votes_dpt_office"
            ),
        }

        # Asegura que devolvemos todas las keys aunque algún campo falte
        empty.update(aggregated)
        return empty

    # ------------------------------------------------------------------
    # Rule engine - PERFORMANCE
    # ------------------------------------------------------------------

    def _build_performance_insights(
        self,
        context: EmployeeInsightContext,
        features: EmployeeInsightFeaturesOut,
    ) -> list[EmployeeInsightItemOut]:
        insights: list[EmployeeInsightItemOut] = []

        current = features.current_evaluation_score_normalized
        previous = features.previous_evaluation_score_normalized
        delta = features.performance_delta_normalized
        band = features.performance_band
        trend = features.performance_trend

        if current is None:
            return insights

        # Si no hay evaluación anterior, no podemos construir la matriz completa.
        # Fallback mínimo: exponer solo la banda actual si quieres mantener algo,
        # pero aquí lo dejamos vacío para que no mezclemos semánticas antiguas.
        if previous is None or delta is None or trend is None or band is None:
            return insights

        evidence = {
            "current_evaluation_at": features.current_evaluation_at,
            "previous_evaluation_at": features.previous_evaluation_at,
            "current_score_normalized": current,
            "previous_score_normalized": previous,
            "delta": delta,
            "performance_band": band,
            "performance_trend": trend,
            "high_threshold": self.rules.high_performance_score,
            "medium_threshold": self.rules.medium_performance_score,
            "trend_threshold": self.rules.performance_delta_threshold,
        }

        # MATRIZ
        if band == "high" and trend in {"up", "flat"}:
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.HIGH_SOLID_PERFORMANCE,
                    family=InsightFamily.PERFORMANCE,
                    title="Alto desempeño sólido",
                    description=(
                        "El empleado se mantiene en nivel alto de desempeño "
                        "y presenta una trayectoria estable o positiva."
                    ),
                    priority=10,
                    evidence=evidence,
                )
            )
        elif band == "high" and trend == "down":
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.HIDDEN_RISK,
                    family=InsightFamily.PERFORMANCE,
                    title="Riesgo oculto",
                    description=(
                        "El empleado sigue en nivel alto, pero su evolución "
                        "muestra una caída relevante respecto al periodo anterior."
                    ),
                    priority=12,
                    evidence=evidence,
                )
            )
        elif band == "medium" and trend == "up":
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.POTENTIAL,
                    family=InsightFamily.PERFORMANCE,
                    title="Potencial",
                    description=(
                        "El empleado se encuentra en un nivel medio actual, "
                        "pero muestra una evolución positiva relevante."
                    ),
                    priority=20,
                    evidence=evidence,
                )
            )
        elif band == "medium" and trend in {"flat", "down"}:
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.STAGNANT,
                    family=InsightFamily.PERFORMANCE,
                    title="Estancado",
                    description=(
                        "El empleado se mantiene en nivel medio sin una mejora "
                        "relevante, o muestra una ligera pérdida de tracción."
                    ),
                    priority=25,
                    evidence=evidence,
                )
            )
        elif band == "low" and trend == "up":
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.RECOVERY,
                    family=InsightFamily.PERFORMANCE,
                    title="Recuperación",
                    description=(
                        "El empleado sigue en nivel bajo actual, pero presenta "
                        "una mejora relevante respecto a la evaluación anterior."
                    ),
                    priority=30,
                    evidence=evidence,
                )
            )
        elif band == "low" and trend in {"flat", "down"}:
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.CRITICAL,
                    family=InsightFamily.PERFORMANCE,
                    title="Crítico",
                    description=(
                        "El empleado se encuentra en nivel bajo y no muestra "
                        "una recuperación relevante en el periodo comparado."
                    ),
                    priority=35,
                    evidence=evidence,
                )
            )

        return insights

    # ------------------------------------------------------------------
    # Rule engine - ONA RELACIONES (people.ona_insights)
    # ------------------------------------------------------------------

    def _build_ona_relationship_insights(
        self,
        context: EmployeeInsightContext,
        features: EmployeeInsightFeaturesOut,
    ) -> list[EmployeeInsightItemOut]:
        insights: list[EmployeeInsightItemOut] = []

        if features.ona_insight_record_count == 0:
            return insights

        category = features.category

        is_socio = category == "Socio" or category is None
        is_estructura = category == "Estructura"
        is_socio_or_estructura = is_socio or is_estructura

        def ge(
            value: float | int | None, threshold: float | int | None
        ) -> bool:
            return (
                value is not None
                and threshold is not None
                and value >= threshold
            )

        def gt(
            value: float | int | None, threshold: float | int | None
        ) -> bool:
            return (
                value is not None
                and threshold is not None
                and value > threshold
            )

        # 1) Influencia en niveles superiores
        #
        # Pseudocódigo:
        # mask_influ_a = (
        #     ~socio
        #     & (df["n_upper_categories_in"] >= 2)
        # )
        if (
            not is_socio
            and features.n_upper_categories_in is not None
            and features.n_upper_categories_in >= 2
        ):
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.UPPER_LEVEL_INFLUENCE,
                    family=InsightFamily.ONA,
                    title="Influencia en niveles superiores",
                    description=(
                        "Este empleado genera reconocimiento en niveles organizativos "
                        "superiores, lo que indica credibilidad y capacidad de impacto "
                        "por encima de su posición formal actual. Es una señal relevante "
                        "de confianza ascendente y posible proyección hacia mayores "
                        "niveles de responsabilidad."
                    ),
                    priority=40,
                    evidence={
                        "formula_description": (
                            "Se identifica cuando el empleado recibe relaciones entrantes "
                            "desde dos o más personas pertenecientes a categorías "
                            "organizativas superiores a la suya."
                        ),
                        "category": features.category,
                        "n_upper_categories_in": features.n_upper_categories_in,
                        "threshold": 2,
                        "excluded_categories": ["Socio", None],
                    },
                )
            )

        # 2) Alta confianza del equipo
        #
        # Pseudocódigo:
        # mask_alta_conf = (
        #     ~socio
        #     & (df["n_respuestas"] >= 3)
        #     & (df["tasa_respuestas"] >= 0.4)
        #     & (df["n_same_dept_office_in_no_ci"] >= 2)
        #     & (
        #         df["n_same_dept_office_in_no_ci"]
        #         >= df["p80_n_same_dept_office_in_no_ci"]
        #     )
        # )
        if (
            not is_socio
            and features.n_respuestas is not None
            and features.n_respuestas >= 3
            and features.tasa_respuestas is not None
            and features.tasa_respuestas >= 0.4
            and features.n_same_dept_office_in_no_ci is not None
            and features.n_same_dept_office_in_no_ci >= 2
            and ge(
                features.n_same_dept_office_in_no_ci,
                features.p80_n_same_dept_office_in_no_ci,
            )
        ):
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.HIGH_TEAM_TRUST,
                    family=InsightFamily.ONA,
                    title="Alta confianza del equipo",
                    description=(
                        "Este empleado concentra un alto nivel de reconocimiento dentro "
                        "de su entorno. Es una señal de confianza, visibilidad y "
                        "relevancia en el día a día del equipo."
                    ),
                    priority=45,
                    evidence={
                        "formula_description": (
                            "Se identifica cuando el empleado recibe dos o más "
                            "nominaciones dentro de su propio equipo, Departamento y "
                            "Oficina, y se sitúa entre el 20% de personas más reconocidas "
                            "de su grupo de referencia Departamento-Oficina."
                        ),
                        "category": features.category,
                        "n_respuestas": features.n_respuestas,
                        "tasa_respuestas": features.tasa_respuestas,
                        "n_same_dept_office_in_no_ci": (
                            features.n_same_dept_office_in_no_ci
                        ),
                        "p80_n_same_dept_office_in_no_ci": (
                            features.p80_n_same_dept_office_in_no_ci
                        ),
                        "min_n_respuestas": 3,
                        "min_tasa_respuestas": 0.4,
                        "min_n_same_dept_office_in_no_ci": 2,
                        "excluded_categories": ["Socio", None],
                    },
                )
            )

        # 3) Liderazgo transversal
        #
        # Pseudocódigo:
        # mask_influ_tf = (
        #     ~socio
        #     & df["influence"].isin(["central", "hipo"])
        #     & (df["n_different_categories_in"] >= 3)
        #     & (
        #         df["n_different_categories_in"]
        #         >= df["p80_n_different_categories_in"]
        #     )
        # )
        if (
            not is_socio
            and features.influence in {"central", "hipo"}
            and features.n_different_categories_in is not None
            and features.n_different_categories_in >= 3
            and ge(
                features.n_different_categories_in,
                features.p80_n_different_categories_in,
            )
        ):
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.TRANSVERSAL_LEADERSHIP,
                    family=InsightFamily.ONA,
                    title="Liderazgo transversal",
                    description=(
                        "Este empleado concentra reconocimiento desde múltiples niveles "
                        "o colectivos de la organización, lo que sugiere una capacidad "
                        "de liderazgo que trasciende de su entorno directo. Es una señal "
                        "de influencia transversal, credibilidad interna y capacidad "
                        "para generar impacto en distintos segmentos organizativos."
                    ),
                    priority=50,
                    evidence={
                        "formula_description": (
                            "Se activa cuando el empleado recibe relaciones entrantes "
                            "desde tres o más categorías organizativas distintas y, "
                            "además, se sitúa entre el 20% con más conexiones dentro "
                            "de su grupo de referencia Departamento-Oficina."
                        ),
                        "category": features.category,
                        "influence": features.influence,
                        "valid_influence_values": ["central", "hipo"],
                        "n_different_categories_in": features.n_different_categories_in,
                        "p80_n_different_categories_in": (
                            features.p80_n_different_categories_in
                        ),
                        "min_n_different_categories_in": 3,
                        "excluded_categories": ["Socio", None],
                    },
                )
            )

        # 4) Influencia en niveles inferiores
        #
        # Pseudocódigo:
        # mask_influ_d = (
        #     ~socio
        #     & (df["n_lower_categories_in"] >= 3)
        # )
        if (
            not is_socio
            and features.n_lower_categories_in is not None
            and features.n_lower_categories_in >= 3
        ):
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.LOWER_LEVEL_INFLUENCE,
                    family=InsightFamily.ONA,
                    title="Influencia en niveles inferiores",
                    description=(
                        "Este empleado genera reconocimiento en niveles organizativos "
                        "inferiores, lo que refleja capacidad de influencia, cercanía "
                        "y referencia profesional."
                    ),
                    priority=55,
                    evidence={
                        "formula_description": (
                            "Se identifica cuando el empleado recibe relaciones entrantes "
                            "desde tres o más personas pertenecientes a categorías "
                            "organizativas inferiores a la suya."
                        ),
                        "category": features.category,
                        "n_lower_categories_in": features.n_lower_categories_in,
                        "threshold": 3,
                        "excluded_categories": ["Socio", None],
                    },
                )
            )

        # 5) Conector de equipo
        #
        # Pseudocódigo:
        # mask_influ_t = (
        #     ~socio
        #     & (df["n_different_categories_in"] >= 2)
        #     & (
        #         df["n_different_categories_in"]
        #         >= df["p80_n_different_categories_in"]
        #     )
        # )
        if (
            not is_socio
            and features.n_different_categories_in is not None
            and features.n_different_categories_in >= 2
            and ge(
                features.n_different_categories_in,
                features.p80_n_different_categories_in,
            )
        ):
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.TEAM_CONNECTOR,
                    family=InsightFamily.ONA,
                    title="Conector de equipo",
                    description=(
                        "Este empleado ayuda a conectar personas dentro del equipo. "
                        "Puede actuar como punto de apoyo informal para que la "
                        "información y la colaboración fluyan mejor."
                    ),
                    priority=60,
                    evidence={
                        "formula_description": (
                            "Se activa cuando el empleado recibe relaciones entrantes "
                            "desde al menos dos categorías organizativas distintas y "
                            "se sitúa entre el 20% de personas con más conexiones "
                            "dentro de su grupo de referencia Departamento-Oficina."
                        ),
                        "category": features.category,
                        "n_different_categories_in": features.n_different_categories_in,
                        "p80_n_different_categories_in": (
                            features.p80_n_different_categories_in
                        ),
                        "min_n_different_categories_in": 2,
                        "excluded_categories": ["Socio", None],
                    },
                )
            )

        # 6) Conector organizativo
        #
        # Pseudocódigo:
        # mask_influ_p = (
        #     ~socio
        #     & (df["n_different_departments_in"] >= 2)
        #     & (
        #         df["n_different_departments_in"]
        #         >= df["p80_n_different_departments_in"]
        #     )
        # )
        if (
            not is_socio
            and features.n_different_departments_in is not None
            and features.n_different_departments_in >= 2
            and ge(
                features.n_different_departments_in,
                features.p80_n_different_departments_in,
            )
        ):
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.ORGANIZATIONAL_CONNECTOR,
                    family=InsightFamily.ONA,
                    title="Conector organizativo",
                    description=(
                        "Este empleado conecta diferentes áreas o departamentos. "
                        "Puede ser clave para facilitar colaboración, circulación "
                        "de información y coordinación transversal."
                    ),
                    priority=65,
                    evidence={
                        "formula_description": (
                            "Se identifica cuando el empleado recibe relaciones "
                            "entrantes desde dos o más departamentos distintos y se "
                            "sitúa entre el 20% de personas con más conexiones dentro "
                            "de su grupo de referencia Departamento-Oficina."
                        ),
                        "category": features.category,
                        "n_different_departments_in": features.n_different_departments_in,
                        "p80_n_different_departments_in": (
                            features.p80_n_different_departments_in
                        ),
                        "min_n_different_departments_in": 2,
                        "excluded_categories": ["Socio", None],
                    },
                )
            )

        # 7) Referente en su nivel
        #
        # Pseudocódigo:
        # socio_estructura = socio | (df["category"] == "Estructura")
        # mask_influ_l = (
        #     ~socio_estructura
        #     & (df["n_same_category_in"] >= 2)
        # )
        if (
            not is_socio_or_estructura
            and features.n_same_category_in is not None
            and features.n_same_category_in >= 2
        ):
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.PEER_LEVEL_INFLUENCE,
                    family=InsightFamily.ONA,
                    title="Referente en su nivel",
                    description=(
                        "Este empleado tiene una influencia fuerte entre personas "
                        "de su mismo nivel o niveles cercanos. Puede ser una "
                        "referencia natural para sus pares."
                    ),
                    priority=70,
                    evidence={
                        "formula_description": (
                            "Se identifica cuando el empleado recibe relaciones "
                            "entrantes desde dos o más personas de su misma categoría "
                            "organizativa o categorías equivalentes."
                        ),
                        "category": features.category,
                        "n_same_category_in": features.n_same_category_in,
                        "threshold": 2,
                        "excluded_categories": ["Socio", "Estructura", None],
                    },
                )
            )

        return insights

    # ------------------------------------------------------------------
    # Rule engine - ONA ACTIVO refinado
    # ------------------------------------------------------------------

    def _build_ona_active_insights(
        self,
        context: EmployeeInsightContext,
        features: EmployeeInsightFeaturesOut,
    ) -> list[EmployeeInsightItemOut]:
        insights: list[EmployeeInsightItemOut] = []

        if features.ona_record_count == 0:
            return insights

        if (
            features.ona_percentile_1 is not None
            and features.ona_percentile_1 >= self.rules.high_ona_percentile
        ):
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.ACTIVE_INFLUENCE_CI,
                    family=InsightFamily.ONA,
                    title="Influencia CI",
                    description=(
                        "El empleado se encuentra en el 20% más alto del "
                        "percentil 1 de ONA activo."
                    ),
                    priority=70,
                    evidence={
                        "ona_percentile_1": features.ona_percentile_1,
                        "threshold": self.rules.high_ona_percentile,
                    },
                )
            )

        if (
            features.ona_percentile_2 is not None
            and features.ona_percentile_2 >= self.rules.high_ona_percentile
        ):
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.ACTIVE_INFLUENCE_AT,
                    family=InsightFamily.ONA,
                    title="Influencia AT",
                    description=(
                        "El empleado se encuentra en el 20% más alto del "
                        "percentil 2 de ONA activo."
                    ),
                    priority=72,
                    evidence={
                        "ona_percentile_2": features.ona_percentile_2,
                        "threshold": self.rules.high_ona_percentile,
                    },
                )
            )

        if (
            features.ona_percentile_3 is not None
            and features.ona_percentile_3 >= self.rules.high_ona_percentile
        ):
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.ACTIVE_INFLUENCE_AP,
                    family=InsightFamily.ONA,
                    title="Influencia AP",
                    description=(
                        "El empleado se encuentra en el 20% más alto del "
                        "percentil 3 de ONA activo."
                    ),
                    priority=74,
                    evidence={
                        "ona_percentile_3": features.ona_percentile_3,
                        "threshold": self.rules.high_ona_percentile,
                    },
                )
            )

        if (
            features.ona_percentile_4 is not None
            and features.ona_percentile_4 >= self.rules.high_ona_percentile
        ):
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.ACTIVE_INFLUENCE_IN,
                    family=InsightFamily.ONA,
                    title="Influencia IN",
                    description=(
                        "El empleado se encuentra en el 20% más alto del "
                        "percentil 4 de ONA activo."
                    ),
                    priority=76,
                    evidence={
                        "ona_percentile_4": features.ona_percentile_4,
                        "threshold": self.rules.high_ona_percentile,
                    },
                )
            )

        return insights

    def _build_ona_and_performance_insights(
        self,
        context: EmployeeInsightContext,
        features: EmployeeInsightFeaturesOut,
    ) -> list[EmployeeInsightItemOut]:

        insights: list[EmployeeInsightItemOut] = []

        score = features.current_evaluation_score_normalized
        ona_category = features.ona_primary_category

        if score is None or ona_category is None:
            return insights

        evidence = {
            "current_evaluation_at": features.current_evaluation_at,
            "current_score_normalized": score,
            "ona_primary_category": ona_category,
            "threshold": self.rules.high_performance_score,
        }

        if (
            score >= self.rules.high_performance_score
            and ona_category == "central"
        ):
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.HIGH_TALENT,
                    family=InsightFamily.TALENT,
                    title="Alto Talento",
                    description=(
                        "El empleado combina un desempeño alto con una posición "
                        "central dentro de la red organizativa."
                    ),
                    priority=15,
                    evidence=evidence,
                )
            )

        elif (
            score >= self.rules.high_performance_score
            and ona_category == "hipo"
        ):
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.HIGH_POTENTIAL,
                    family=InsightFamily.TALENT,
                    title="Alto Potencial",
                    description=(
                        "El empleado presenta desempeño alto y una clasificación "
                        "ONA consistente con alto potencial."
                    ),
                    priority=16,
                    evidence=evidence,
                )
            )

        elif score < self.rules.high_performance_score and ona_category in {
            "central",
            "hipo",
        }:
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.HIGH_UNDERRECOGNIZED,
                    family=InsightFamily.TALENT,
                    title="Alto Infrareconocido",
                    description=(
                        "El empleado presenta una posición ONA fuerte, pero su "
                        "desempeño actual no alcanza el umbral alto."
                    ),
                    priority=17,
                    evidence=evidence,
                )
            )

        elif score >= self.rules.high_performance_score and ona_category in {
            "intermediary",
            "peripheral",
        }:
            insights.append(
                EmployeeInsightItemOut(
                    code=InsightCode.HIGH_PERFORMER,
                    family=InsightFamily.TALENT,
                    title="Alto Rendimiento",
                    description=(
                        "El empleado presenta desempeño alto con una clasificación "
                        "ONA de tipo intermediary o peripheral."
                    ),
                    priority=18,
                    evidence=evidence,
                )
            )

        return insights

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_performance_band(self, score: float | None) -> str | None:
        if score is None:
            return None

        if score >= self.rules.high_performance_score:
            return "high"

        if score >= self.rules.medium_performance_score:
            return "medium"

        return "low"

    def _get_performance_trend(self, delta: float | None) -> str | None:
        if delta is None:
            return None

        if delta >= self.rules.performance_delta_threshold:
            return "up"

        if delta <= -self.rules.performance_delta_threshold:
            return "down"

        return "flat"

    def _normalize_percentile(self, value: float | None) -> float | None:
        if value is None:
            return None
        if 0 <= value <= 1:
            return round(value * 100, 2)
        return round(value, 2)

    def _normalize_performance_score(
        self,
        value: float | None,
    ) -> float | None:
        """
        Normaliza score de desempeño a una escala aproximada 0..100.

        Suposiciones:
        - 0..1  -> porcentaje * 100
        - 0..5  -> escala HR típica, se convierte a 0..100
        - >5    -> se asume que ya viene en 0..100
        """
        if value is None:
            return None

        if 0 <= value <= 1:
            return round(value * 100, 2)

        if 0 < value <= 5:
            return round((value / 5) * 100, 2)

        return round(value, 2)
