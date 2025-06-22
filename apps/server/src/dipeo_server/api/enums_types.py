import strawberry
from enum import Enum

from dipeo_server.core import DiagramFormat as DomainDiagramFormat

DiagramFormat = strawberry.enum(DomainDiagramFormat)
