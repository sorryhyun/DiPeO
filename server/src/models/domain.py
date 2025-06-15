"""
Domain models that match the frontend's DomainDiagram structure.
These models use dictionaries (Records) with IDs as keys instead of arrays.
"""
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# Base types
NodeID = str
ArrowID = str
HandleID = str
PersonID = str
ApiKeyID = str

# Handle model
class DomainHandle(BaseModel):
    id: HandleID
    nodeId: NodeID
    label: str
    direction: str  # "input" | "output"
    dataType: str = "any"
    position: Optional[str] = None  # "left" | "right" | "top" | "bottom"

# Node model
class DomainNode(BaseModel):
    id: NodeID
    type: str  # "start", "person_job", "condition", etc.
    position: Dict[str, float]  # {"x": float, "y": float}
    data: Dict[str, Any]

# Arrow model
class DomainArrow(BaseModel):
    id: ArrowID
    source: HandleID  # "nodeId:handleName" format
    target: HandleID  # "nodeId:handleName" format
    data: Optional[Dict[str, Any]] = None

# Person model
class DomainPerson(BaseModel):
    id: PersonID
    label: str
    service: str  # "openai", "claude", "gemini", "grok"
    model: str
    apiKeyId: ApiKeyID  # Reference to ApiKey by ID
    systemPrompt: Optional[str] = None
    forgettingMode: str = "no_forget"
    type: str = "person"

# API Key model
class DomainApiKey(BaseModel):
    id: ApiKeyID
    label: str
    service: str
    key: str  # Actual API key (masked in listings)

# Diagram metadata
class DiagramMetadata(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    version: str = "2.0.0"
    created: str = Field(default_factory=lambda: datetime.now().isoformat())
    modified: str = Field(default_factory=lambda: datetime.now().isoformat())
    author: Optional[str] = None
    tags: Optional[List[str]] = None

# Main diagram model
class DomainDiagram(BaseModel):
    nodes: Dict[NodeID, DomainNode]
    handles: Dict[HandleID, DomainHandle]
    arrows: Dict[ArrowID, DomainArrow]
    persons: Dict[PersonID, DomainPerson]
    apiKeys: Dict[ApiKeyID, DomainApiKey]
    metadata: Optional[DiagramMetadata] = None

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )