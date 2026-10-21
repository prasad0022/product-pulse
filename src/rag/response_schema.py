from pydantic import BaseModel, Field
from typing import List

class Source(BaseModel):
    source_id: str
    title: str

class InvestigationResponse(BaseModel):
    findings: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    root_cause_candidates: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    sources: List[Source] = Field(default_factory=list)
    disclaimer: str = "Decision-support output; root-cause candidates require validation."
