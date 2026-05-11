from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EvaluationScatterPointOut(BaseModel):
    employee_id: int
    society_id: Optional[int] = None
    department_id: Optional[int] = None
    category_id: Optional[int] = None

    evaluation_id: int
    evaluation_at: datetime
    evaluation_year: int

    final_score: float
    overall_percentile: Optional[float] = None


class EvaluationScatterLatestCycleOut(BaseModel):
    cycle_year: int
    cycle_label: str
    total_points: int
    points: list[EvaluationScatterPointOut]
