from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str  # "current", "future", "high_cost", "intervention"
    probability: float = 1.0
    annual_cost: float = 0.0
    oop_estimate: float = 0.0
    year: int = 0


class GraphEdge(BaseModel):
    source: str
    target: str
    edge_type: str  # "progression", "comorbidity", "intervention", "cost"
    probability: float = 0.0
    label: str = ""


class CarePathwayGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    total_5yr_cost: float = 0.0
    total_5yr_oop: float = 0.0
