from pydantic import BaseModel


class OnaRelationsOut(BaseModel):

    from_employee_id: int
    to_employee_id: int
    ona_question_id: int


class OnaActiveOut(BaseModel):

    employee_id: int
    percentile_1: float
    percentile_2: float
    percentile_3: float
    percentile_4: float
    closeness_centrality: float
    betweenness_centrality: float | None
    eigenvector_centrality:  float | None

    ona_influence_id: int
    ona_category_id: int
    degree_centrality: float
