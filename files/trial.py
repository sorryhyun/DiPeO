from __future__ import annotations
from typing import List, Dict, Optional, Union, Annotated, Literal
from pydantic import BaseModel, Field, model_validator, field_validator

# ------- Enums -------
NodeKind = Literal["start","db","code_job","template_job","person_job","condition","sub_diagram","endpoint"]
PayloadType = Literal["raw_text","json","conversation_state","bytes"]  # 확장 여지
MemoryProfile = Literal["GOLDFISH","FULL"]

# ------- Common -------
class Position(BaseModel):
    x: int
    y: int

# ------- Props by node -------
class StartProps(BaseModel):
    custom_data: Optional[Dict[str, object]] = None

class DBProps(BaseModel):
    operation: Literal["read","write"]
    sub_type: Literal["file"]  # 확장 가능
    source_details: Optional[Union[str, List[str]]] = None
    file: Optional[str] = None
    serialize_json: Optional[bool] = None

class CodeJobProps(BaseModel):
    language: Literal["python","bash"]
    filePath: Optional[str] = None
    functionName: Optional[str] = None
    code: Optional[str] = None
    # 안전성
    timeout_sec: int = 60
    retries: int = 0
    cwd: Optional[str] = None
    allow_network: bool = False

class TemplateJobProps(BaseModel):
    engine: Literal["jinja2"] = "jinja2"
    template_path: str
    output_path: str
    variables: Optional[Dict[str, object]] = None
    autoescape: bool = True

class PersonJobProps(BaseModel):
    default_prompt: str
    max_iteration: int = 1
    memory_profile: MemoryProfile = "GOLDFISH"
    person: str  # persons dict 키 참조
    flipped: Optional[Union[bool, List[bool]]] = None
    first_only_prompt: Optional[str] = None

class ConditionProps(BaseModel):
    condition_type: Literal["detect_max_iterations"]
    flipped: Optional[Union[bool, List[bool]]] = None

class SubDiagramProps(BaseModel):
    diagram_name: str
    diagram_format: Literal["light"] = "light"
    passInputData: bool = False
    ignoreIfSub: bool = False
    # 배치 실행
    mode: Literal["single","map"] = "single"
    batch_input_key: Optional[str] = None
    batch_parallel: Optional[bool] = None

class EndpointProps(BaseModel):
    file_format: Optional[str] = "txt"
    file_path: Optional[str] = None
    save_to_file: bool = False
    flipped: Optional[Union[bool, List[bool]]] = None

# ------- Node union -------
class NodeBase(BaseModel):
    id: Optional[str] = None     # 신규: 내부 참조용
    label: str                   # 표시용
    type: NodeKind
    position: Position

class StartNode(NodeBase):
    type: Literal["start"]
    props: StartProps = StartProps()

class DBNode(NodeBase):
    type: Literal["db"]
    props: DBProps

class CodeJobNode(NodeBase):
    type: Literal["code_job"]
    props: CodeJobProps

class TemplateJobNode(NodeBase):
    type: Literal["template_job"]
    props: TemplateJobProps

class PersonJobNode(NodeBase):
    type: Literal["person_job"]
    props: PersonJobProps

class ConditionNode(NodeBase):
    type: Literal["condition"]
    props: ConditionProps

class SubDiagramNode(NodeBase):
    type: Literal["sub_diagram"]
    props: SubDiagramProps

class EndpointNode(NodeBase):
    type: Literal["endpoint"]
    props: EndpointProps

Node = Annotated[
    Union[
        StartNode, DBNode, CodeJobNode, TemplateJobNode,
        PersonJobNode, ConditionNode, SubDiagramNode, EndpointNode
    ],
    Field(discriminator="type")
]

# ------- Connections -------
class Connection(BaseModel):
    source: str = Field(validation_alias="from", serialization_alias="from")
    target: str = Field(validation_alias="to", serialization_alias="to")
    label: Optional[str] = None
    content_type: Optional[PayloadType] = None
    # 선택: 강한 타입 검증을 원하면 추가
    schema_ref: Optional[str] = None  # JSONSchema 경로 또는 ID

# ------- Persons -------
class PersonConfig(BaseModel):
    service: Literal["openai","anthropic","bedrock","azure_openai"] = "openai"
    model: str
    system_prompt: Optional[str] = None
    api_key_id: str

# ------- Diagram -------
class Diagram(BaseModel):
    version: Literal["light"] = "light"
    nodes: List[Node]
    connections: List[Connection]
    persons: Optional[Dict[str, PersonConfig]] = None

    @model_validator(mode="after")
    def _validate_graph(self):
        ids = []
        labels = []
        for n in self.nodes:
            # id 기본값 = slug(label)
            if not n.id:
                n.id = n.label.replace(" ", "_").lower()
            ids.append(n.id)
            labels.append(n.label)
        if len(set(labels)) != len(labels):
            raise ValueError("node label 중복")
        # 연결 대상 검증 (라벨 기준 호환)
        label_set = set(labels)
        for e in self.connections:
            if e.source not in label_set or e.target not in label_set:
                raise ValueError(f"엣지가 존재하지 않는 노드를 참조: {e}")
        return self
