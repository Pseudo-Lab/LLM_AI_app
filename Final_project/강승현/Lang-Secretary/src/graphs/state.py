from typing import TypedDict


class GraphState(TypedDict):
    user_input: str
    route: str
    final_answer: str

    paper_arxiv_id: str
    paper_duplicated_check: str # bool
    paper_summary: str