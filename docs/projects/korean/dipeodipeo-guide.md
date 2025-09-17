# DiPeO AI 다이어그램 생성 가이드

## 개요

`dipeodipeo` 프로젝트는 AI를 이용해 기존 DiPeO 다이어그램에서 새로운 DiPeO 다이어그램을 자동으로 만들어, 플랫폼의 궁극적인 도그푸딩(dogfooding) 비전을 보여 줍니다. 구조화된 출력을 지원하는 대규모 언어 모델(LLM)을 활용해 자연어 요구사항을 실행 가능한 워크플로로 변환하는 메타 프로그래밍 접근법입니다.

**핵심 성과**: DiPeO는 이제 자체 도구만으로 스스로를 확장할 수 있을 만큼 성숙해졌습니다. AI 에이전트가 새로운 자동화 워크플로를 설계하며 자기 향상 루프를 형성합니다.

## 시스템 아키텍처

```
자연어 요청 → 프롬프트 엔지니어링 → AI 다이어그램 생성 → 후처리 → 실행 가능한 다이어그램
                                   ↓
                          테스트 데이터 생성
```

이 시스템은 세 가지 전문화된 AI 에이전트를 하나의 파이프라인으로 오케스트레이션합니다.

1. **프롬프트 엔지니어**: 사용자 요구사항을 세밀한 생성 프롬프트로 변환합니다.
2. **다이어그램 디자이너**: 모범 사례를 따르는 구조화된 DiPeO 다이어그램을 작성합니다.
3. **테스트 데이터 생성기**: 생성된 다이어그램을 검증할 현실적인 테스트 데이터를 준비합니다.

## 핵심 구성 요소

### 1. 라이트 다이어그램 모델(`light_diagram_models.py`)

LLM이 구조화된 출력을 내보낼 수 있도록 Pydantic 기반 스키마를 정의합니다.

```python
# 각 DiPeO 노드 타입에 대한 타입화된 노드 클래스
class PersonJobNode(BaseModel):
    label: str
    type: Literal[LightNodeType.PERSON_JOB]
    position: Position
    props: PersonJobNodeData

# 완전한 다이어그램 명세
class LightDiagram(BaseModel):
    version: Literal["light"] = "light"
    name: str
    description: str
    nodes: List[LightNode]
    connections: List[LightConnection]
    persons: Optional[Dict[str, LightPerson]]
```

**주요 특징**

- DiPeO가 생성한 도메인 모델을 상속해 일관성을 유지합니다.
- 생성 결과를 간결하게 유지하기 위해 중복 필드(예: props의 `label`)를 제거했습니다.
- 다이어그램의 정확성을 확보하는 검증 로직을 포함합니다.
- AI가 생성한 출력에도 타입 안전성을 제공합니다.

### 2. 생성 파이프라인(`test.light.yaml`)

전체 생성 과정을 오케스트레이션하는 핵심 워크플로입니다.

```yaml
nodes:
  - label: load_request
    type: code_job
    # 파일 또는 입력으로부터 사용자 요구사항 로드
  
  - label: generate_prompt
    type: person_job
    # 다이어그램 생성을 위한 최적화 프롬프트를 AI가 생성
    
  - label: generate_test_data
    type: person_job  
    # 워크플로용 테스트 데이터를 AI가 생성
    
  - label: generate_diagram
    type: person_job
    # 실제 DiPeO 다이어그램을 AI가 생성
    
  - label: format_yaml
    type: code_job
    # YAML 출력을 정리하는 후처리
```

### 3. 후처리(`process.py`)

AI가 만들어 낸 다이어그램을 정리하고 서식을 맞춥니다.

```python
def process_diagram(inputs: Dict[str, Any]) -> str:
    # null 값과 빈 컬렉션 제거
    # 가독성을 위한 code 필드 포맷 수정
    # 키를 논리적 순서(version, name, description 등)로 정렬
    # 적절한 멀티라인 문자열을 사용해 깔끔한 YAML 생성
```

**적용된 개선 사항**

- AI가 생성한 불필요한 null 필드를 제거합니다.
- 이스케이프된 줄바꿈을 올바른 멀티라인 YAML로 정리합니다.
- 키가 항상 일정한 순서를 유지하도록 정렬합니다.
- 코드 블록에는 리터럴 스칼라 형식(`|`)을 사용합니다.

### 4. 프롬프트 템플릿(`prompts/`)

#### `diagram_generator.txt`

AI 다이어그램 생성을 위한 포괄적 지침:

* 콘텐츠 타입 규칙(절대 `empty` 사용 금지)
* 노드 배치 가이드라인(x는 200–300씩 증가)
* 노드 선택 모범 사례
* 일반 작업을 위한 코드 패턴
* 오류 처리 요구사항

#### `prompt_generator.txt`

프롬프트 엔지니어 에이전트가 효과적 프롬프트를 만들도록 안내

#### `test_data_generator.txt`

다양한 포맷의 현실적인 테스트 데이터 생성 지침

## 생성 워크플로

### 1단계: 요구사항 정의

워크플로 설명을 `request.txt`에 작성하거나 업데이트합니다.

```text
다음과 같은 데이터 처리 파이프라인을 만들어라:
1. 디렉터리에서 CSV 파일을 로드
2. 데이터 형식 검증
3. 각 파일을 병렬 처리
4. 결과 집계
5. JSON으로 저장
```

### 2단계: 생성 실행

```bash
dipeo run projects/dipeodipeo/test --light --debug --timeout=60
```

### 3단계: 생성된 파일 검토

**생성된 다이어그램**: `projects/dipeodipeo/generated/diagram.light.yaml`

- 실행 가능한 완전한 DiPeO 다이어그램입니다.
- YAML 규칙에 맞게 정돈된 형식으로 저장됩니다.
- 필요한 노드 구성을 모두 포함합니다.

**테스트 데이터**: `projects/dipeodipeo/generated/test_data.csv`

- 테스트에 바로 활용할 수 있는 현실적인 샘플 데이터입니다.
- 기대하는 입력 포맷과 정확히 일치합니다.
- 생성된 다이어그램과 곧바로 연동할 수 있습니다.

### 4단계: 생성된 다이어그램 실행

```bash
dipeo run projects/dipeodipeo/generated/diagram --light --debug
```

## 고급 기능

### 동적 입력 지원

파일을 읽는 대신 런타임 파라미터를 입력으로 받을 수 있습니다:

```bash
dipeo run projects/dipeodipeo/test --light \
  --input-data '{"user_requirements": "웹 스크레이핑 워크플로 생성", "workflow_description": "전자상거래 사이트에서 상품 데이터를 스크레이핑"}'
```

### 사용자 지정 AI 모델

`test.light.yaml`에서 서로 다른 LLM 제공자와 모델을 설정:

```yaml
persons:
  diagram_designer:
    service: anthropic  # 또는 openai, ollama
    model: claude-3-sonnet
    api_key_id: APIKEY_ANTHROPIC
```

### Pydantic 기반 구조화 출력

이 시스템은 OpenAI의 구조화 출력 기능과 Pydantic 모델을 사용하여 다음을 보장합니다:

* 유효한 다이어그램 구문
* 타입 안전한 노드 속성
* 올바른 연결 정의
* 필수 필드 누락 방지

### 테스트 데이터 모델(`test_data_models.py`)

테스트 데이터 생성을 위한 Pydantic 스키마를 정의:

```python
class DataRecord(BaseModel):
    id: str
    name: str
    value: float
    timestamp: str

class TestDataResponse(BaseModel):
    records: List[DataRecord]
    metadata: Dict[str, Any]
```

## 모범 사례 및 지침

### 1. AI 에이전트 구성

**프롬프트 엔지니어**:

* 명확성과 구체성에 집중
* 복잡한 요구사항을 분해
* 구현 힌트 추가

**다이어그램 디자이너**:

* DiPeO 규약을 엄격히 준수
* 적절한 노드 배치 보장
* 더는 사용되지 않는 기능(Deprecated) 사용 금지

**테스트 데이터 생성기**:

* 의미 있고 현실적인 데이터 생성
* 지정된 스키마 준수
* 엣지 케이스 포함

### 2. 콘텐츠 타입 규칙

시스템은 엄격한 콘텐츠 타입 사용을 강제합니다:

* `raw_text` - 일반 텍스트, CSV, 비정형 데이터
* `object` - 구조화 데이터(JSON, 딕셔너리)
* `conversation_state` - LLM 대화 컨텍스트
* **절대** `empty` 금지 - 의미 없는 값

### 3. 노드 선택 전략

* **code\_job** - 모든 데이터 처리와 변환
* **person\_job** - AI 분석이 필요할 때만
* **db** - 파일 I/O 작업
* **sub\_diagram 금지** - 대신 code\_job에서 asyncio 사용

### 4. 오류 처리

생성된 다이어그램에는 다음이 포함됩니다:

* 데이터 로드 후 검증 노드
* 오류 분기를 위한 조건 노드
* 코드의 try-except 블록
* 상세 로깅

## DiPeO 생태계와의 통합

### 코드 생성과의 관계

`/projects/codegen/`이 TypeScript 스펙으로부터 DiPeO의 내부 코드를 생성하는 동안, `dipeodipeo`는 자연어로부터 사용자 지향 다이어그램을 생성합니다. 이 둘은 다음을 함께 시연합니다:

* **codegen**: DiPeO가 스스로를 구축함(인프라)
* **dipeodipeo**: DiPeO가 스스로를 확장함(사용자 워크플로)

### 도그푸딩 계층

```
레벨 1: DiPeO가 다이어그램을 실행(기본 기능)
레벨 2: DiPeO 다이어그램이 DiPeO 코드를 생성(codegen)
레벨 3: DiPeO 다이어그램이 새로운 DiPeO 다이어그램을 생성(dipeodipeo)
```

이 재귀적 능력은 플랫폼의 성숙도와 유연성을 입증합니다.

## 일반 사용 사례

### 1. 빠른 프로토타이핑

아이디어를 몇 초 만에 동작하는 다이어그램으로 변환:

```bash
echo "고객 리뷰의 감성을 분석하는 워크플로를 만들어라" > request.txt
dipeo run projects/dipeodipeo/test --light
```

### 2. 대량 다이어그램 생성

여러 관련 다이어그램을 프로그래밍 방식으로 생성:

```python
workflows = [
    "데이터 검증 파이프라인",
    "리포트 생성 시스템",
    "API 통합 워크플로"
]

for workflow in workflows:
    # 서로 다른 입력으로 생성 실행
    subprocess.run([
        "dipeo", "run", "projects/dipeodipeo/test",
        "--light", "--input-data", 
        json.dumps({"user_requirements": workflow})
    ])
```

### 3. 템플릿 생성

복잡한 다이어그램의 출발점으로 활용:

1. AI로 기본 구조 생성
2. 수동으로 정교화 및 확장
3. 도메인 특화 로직 추가

## 한계와 고려 사항

### 현재 한계

1. **복잡도 상한**: 매우 복잡한 다단계 워크플로는 수동 보정이 필요할 수 있음
2. **도메인 지식**: AI가 특수한 비즈니스 로직을 이해하지 못할 수 있음
3. **성능 최적화**: 대규모 데이터에 대해 생성된 코드는 최적화가 필요할 수 있음
4. **보안**: 생성된 코드를 항상 보안 관점에서 검토해야 함

### 수동 생성이 적절한 경우

* 정밀한 제어가 필요한 미션 크리티컬 워크플로
* 고도로 최적화된 성능 요구
* 외부 시스템과의 복잡한 통합
* 민감한 보안 요구가 있는 워크플로

## 문제 해결

### 생성된 다이어그램이 실행되지 않음

1. 구문 오류 확인:

   ```bash
   dipeo run projects/dipeodipeo/generated/diagram --light --validate-only
   ```
2. 참조된 모든 파일의 존재 확인
3. API 키 설정 확인
4. 연결 라벨이 노드 기대치와 일치하는지 확인

### AI 생성 품질 문제

1. `request.txt`의 프롬프트를 개선
2. 프롬프트 템플릿에 구체적 예시 추가
3. 더 강력한 모델(GPT-4, Claude) 사용
4. 컨텍스트 제공을 위해 샘플 테스트 데이터 제공

### 후처리 오류

`format_yaml`이 실패할 경우:

1. 원시 AI 출력을 확인하여 잘못된 YAML 검사
2. Pydantic 모델이 현재 DiPeO 스키마와 일치하는지 검증
3. 새로운 노드 유형에 맞게 `process.py` 업데이트

## 향후 개선

### 계획된 기능

1. **다이어그램 최적화**: AI가 기존 다이어그램을 분석하고 최적화
2. **오류 복구**: 실패한 생성에 대한 자동 수정 시도
3. **학습 시스템**: 성공 패턴에 기반한 프롬프트 개선
4. **시각적 미리보기**: 실행 전 다이어그램 미리보기 생성

### 연구 방향

* 복잡한 워크플로를 위한 멀티 에이전트 협업
* DiPeO 생성에 특화된 파인튜닝 모델
* 속성 기반 테스트를 활용한 자동 테스트 케이스 생성
* 실패에 적응하는 자기 치유(Self-healing) 다이어그램

## 결론

`dipeodipeo` 프로젝트는 DiPeO의 자기 참조적 능력의 정점을 보여줍니다. AI 기반 DiPeO 다이어그램을 사용해 새로운 DiPeO 다이어그램을 생성함으로써, 플랫폼이 스스로를 확장하고 개선하는 강력한 피드백 루프를 형성합니다. 사용자는 원하는 것을 자연어로 설명하기만 하면 즉시 실행 가능한 솔루션을 받게 됩니다.

이 시스템의 구조화된 출력 접근, 포괄적 검증, 후처리는 생성된 다이어그램이 구문적으로 올바를 뿐 아니라 모범 사례를 따르며 즉시 실행 가능하도록 보장합니다. 이는 비기술 사용자에게도 DiPeO를 접근 가능하게 하면서, 개발자가 기대하는 강력함과 유연성을 유지합니다.
