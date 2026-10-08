from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    filename: str
    extension: str
    size_bytes: Optional[int] = None
    character_count: int = 0
    word_count: int = 0
    extra: Dict[str, Any] = Field(default_factory=dict)

class ProcessedDocument(BaseModel):
    document_id: str
    filename: str
    text: str
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Claim(BaseModel):
    claim_id: str
    claim: str
    document_id: str
    source: str
    confidence: float = 1.0

class EvidenceItem(BaseModel):
    evidence_id: str
    text: str
    document_id: str
    source: str
    confidence: float = 1.0

class EventItem(BaseModel):
    event_id: str
    date: Optional[str] = None
    event: str
    document_id: str
    source: str
    confidence: float = 1.0

class GraphNode(BaseModel):
    id: str
    type: str  # "document", "claim", "evidence", "event"
    label: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphRelationship(BaseModel):
    source: str
    target: str
    type: str  # DOCUMENT_CONTAINS_CLAIM, DOCUMENT_CONTAINS_EVIDENCE, DOCUMENT_CONTAINS_EVENT, CLAIM_SUPPORTED_BY_EVIDENCE, CLAIM_ASSOCIATED_WITH_EVENT, EVIDENCE_ASSOCIATED_WITH_EVENT
    properties: Dict[str, Any] = Field(default_factory=dict)

class EvidenceGraph(BaseModel):
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]

class TimelineEvent(BaseModel):
    event_id: str
    date: Optional[str] = None
    event: str
    source: str
    document_id: Optional[str] = None
    raw_date: Optional[str] = None
    is_date_valid: bool = True
