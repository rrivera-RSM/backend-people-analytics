from __future__ import annotations

from dataclasses import dataclass

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.infrastructure.db.models.core.employee import Employee
from app.infrastructure.db.models.people.evaluation import Evaluation
from app.infrastructure.db.models.people.ona_active import OnaActive
from app.infrastructure.db.models.people.ona_insights import OnaInsights


class InsightFamily(str, Enum):
    PERFORMANCE = "performance"
    ONA = "ona"
    TALENT = "talent"


class InsightCode(str, Enum):

    HIGH_SOLID_PERFORMANCE = "high_solid_performance"
    HIDDEN_RISK = "hidden_risk"
    POTENTIAL = "potential"
    STAGNANT = "stagnant"
    RECOVERY = "recovery"
    CRITICAL = "critical"

    # --- ONA RELACIONES (nueva tabla people.ona_insights) ---
    UPPER_LEVEL_INFLUENCE = "upper_level_influence"
    HIGH_TEAM_TRUST = "high_team_trust"
    TRANSVERSAL_LEADERSHIP = "transversal_leadership"
    LOWER_LEVEL_INFLUENCE = "lower_level_influence"
    TEAM_CONNECTOR = "team_connector"
    ORGANIZATIONAL_CONNECTOR = "organizational_connector"
    PEER_LEVEL_INFLUENCE = "peer_level_influence"

    # --- ONA ACTIVO refinado ---
    ACTIVE_INFLUENCE_CI = "active_influence_ci"
    ACTIVE_INFLUENCE_AT = "active_influence_at"
    ACTIVE_INFLUENCE_AP = "active_influence_ap"
    ACTIVE_INFLUENCE_IN = "active_influence_in"

    # --- Desempeño combinado con ONA ---
    HIGH_TALENT = "high_talent"
    HIGH_POTENTIAL = "high_potential"
    HIGH_UNDERRECOGNIZED = "high_underrecognized"
    HIGH_PERFORMER = "high_performer"


class EmployeeInsightItemOut(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    code: InsightCode
    family: InsightFamily
    title: str
    description: str
    priority: int = Field(..., ge=1, le=100)
    evidence: dict[str, Any] = Field(default_factory=dict)


class EmployeeInsightFeaturesOut(BaseModel):
    # ------------------------------------------------------------------
    # Estado empleado
    # ------------------------------------------------------------------
    employee_active: bool
    category: str | None = None
    # ------------------------------------------------------------------
    # PERFORMANCE
    # ------------------------------------------------------------------
    current_evaluation_at: datetime | None = None
    previous_evaluation_at: datetime | None = None

    current_evaluation_score_raw: float | None = None
    previous_evaluation_score_raw: float | None = None
    current_evaluation_score_normalized: float | None = None
    previous_evaluation_score_normalized: float | None = None
    performance_delta_normalized: float | None = None

    performance_band: str | None = None
    performance_trend: str | None = None

    # ------------------------------------------------------------------
    # ONA ACTIVO
    # ------------------------------------------------------------------
    ona_record_count: int = 0
    ona_category_ids: list[int] = Field(default_factory=list)
    ona_influence_ids: list[int] = Field(default_factory=list)

    ona_percentile_1: float | None = None
    ona_percentile_2: float | None = None
    ona_percentile_3: float | None = None
    ona_percentile_4: float | None = None

    ona_primary_category: str | None = None

    degree_centrality: float | None = None
    closeness_centrality: float | None = None
    betweenness_centrality: float | None = None
    eigenvector_centrality: float | None = None

    # ------------------------------------------------------------------
    # ONA RELACIONES (people.ona_insights)
    # ------------------------------------------------------------------
    ona_insight_record_count: int = 0
    ona_insight_categories: list[str] = Field(default_factory=list)

    # --- CORE METRICS ---
    n_different_categories_in: float | None = None
    n_same_category_in: float | None = None
    n_upper_categories_in: float | None = None
    n_lower_categories_in: float | None = None
    n_different_departments_in: float | None = None

    # --- PARTICIPACIÓN / CALIDAD MUESTRA ---
    n_respuestas: float | None = None
    tasa_respuestas: float | None = None

    # --- CONTEXTO DE REFERENCIA (percentiles) ---
    n_same_dept_office_in_no_ci: float | None = None
    p80_n_same_dept_office_in_no_ci: float | None = None

    p80_n_different_categories_in: float | None = None
    p80_n_different_departments_in: float | None = None

    # --- LEGACY (puedes deprecar luego) ---
    n_total_votes_in: float | None = None
    percentile_80_votes_dpt_office: float | None = None

    # --- CLASIFICACIÓN GLOBAL ---
    influence: str | None = None  # (central / hipo / etc.)

    # ------------------------------------------------------------------
    # RELACIONES CRUDAS (para debug / exploración)
    # ------------------------------------------------------------------
    incoming_unique_relations: int = 0
    outgoing_unique_relations: int = 0
    unique_relations: int = 0


class EmployeeInsightsResponseOut(BaseModel):
    generated_at: datetime
    as_of: datetime
    employee_id: int
    employee_full_name: str
    features: EmployeeInsightFeaturesOut
    insights: list[EmployeeInsightItemOut]
    warnings: list[str] = Field(default_factory=list)


@dataclass(slots=True)
class EmployeeInsightContext:
    employee: Employee
    current_evaluation: Evaluation | None
    previous_evaluation: Evaluation | None
    ona_records: list[OnaActive]
    ona_insight_records: list[OnaInsights]
    incoming_unique_relations: int
    outgoing_unique_relations: int
    unique_relations: int
