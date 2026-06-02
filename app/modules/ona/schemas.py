from decimal import Decimal

from pydantic import BaseModel


class OnaRelationsOut(BaseModel):

    from_employee_id: int
    to_employee_id: int
    ona_question_id: int
    from_ona_category: str | None = None
    to_ona_category: str | None = None


class OnaGraphNodeOut(BaseModel):
    employee_id: int
    ona_category: str | None = None
    graph_x_coordinate: Decimal | None = None
    graph_y_coordinate: Decimal | None = None


class OnaGraphEdgeOut(BaseModel):
    from_id: int
    to_id: int


class OnaGraphOut(BaseModel):
    nodes: list[OnaGraphNodeOut]
    edges: list[OnaGraphEdgeOut]


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
