"""
MEPS Data Loader

Loads and queries the pre-processed MEPS data for condition costs
and transition probabilities.

TODO: Implement once MEPS data is downloaded and pre-processed.
Current simulation engine uses hardcoded placeholder values.
"""


def load_transition_matrix(path: str = "data/processed/transitions.parquet"):
    """Load the condition transition probability matrix from processed MEPS data."""
    raise NotImplementedError("MEPS data pipeline not yet built")


def load_cost_distributions(path: str = "data/processed/costs.parquet"):
    """Load cost distribution models from processed MEPS data."""
    raise NotImplementedError("MEPS data pipeline not yet built")


def query_cost(conditions: list[str], age: int, insurance_type: str) -> dict:
    """Query expected cost distribution for a patient profile."""
    raise NotImplementedError("MEPS data pipeline not yet built")
