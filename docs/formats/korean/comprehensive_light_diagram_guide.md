# 종합 DiPeO 라이트 다이어그램 가이드

> **최종 업데이트**: 2025년 1월\
> **최근 변경 사항**:
>
> - 누락된 노드 타입 추가: `HOOK`, `INTEGRATED_API`, `JSON_SCHEMA_VALIDATOR`, `TYPESCRIPT_AST`, `PERSON_BATCH_JOB`
> - `person_job` 노드의 `CUSTOM` 메모리 프로파일 문서화
> - 하위 호환 필드 매핑 명확화 (`source_details` ⟷ `file`, `language` ⟷ `code_type`)
> - 기본 모델 참조를 `gpt-5-nano-2025-08-07`로 업데이트
> - `memory_settings` 뷰 옵션 문서 추가

## 목차

1. [소개](#소개)
2. [핵심 개념](#핵심-개념)
3. [노드 타입 레퍼런스](#노드-타입-레퍼런스)
4. [데이터 흐름과 변수 해석](#데이터-흐름과-변수-해석)
5. [고급 패턴](#고급-패턴)
6. [서브 다이어그램과 모듈 조합](#서브-다이어그램과-모듈-조합)
7. [에러 처리와 복원력](#에러-처리와-복원력)
8. [성능 최적화](#성능-최적화)
9. [모범 사례](#모범-사례)
10. [프로덕션 패턴](#프로덕션-패턴)
11. [디버깅과 트러블슈팅](#디버깅과-트러블슈팅)

## 소개

DiPeO Light 형식은 실행 가능한 다이어그램을 만들기 위한 사람 친화적 YAML 문법입니다. 빠른 프로토타이핑, 복잡한 오케스트레이션, 프로덕션 워크플로까지 설계되었습니다. 이 가이드는 DiPeO의 자체 코드 생성 시스템에서 사용하는 기본 개념부터 고급 패턴까지 모두 다룹니다.

### 핵심 원칙

1. **라벨 기반 아이덴티티**: 노드는 UUID 대신 사람이 읽을 수 있는 라벨로 식별됩니다.
2. **명시적 데이터 흐름**: 연결 라벨은 다운스트림 노드에서의 변수명을 정의합니다.
3. **타입 안정성**: 각 노드 타입은 고유한 속성과 검증 규칙을 갖습니다.
4. **합성 가능성**: 다이어그램은 서브 다이어그램을 통해 중첩·조합할 수 있습니다.
5. **시각적 실행**: 모든 다이어그램은 실시간으로 시각화하고 모니터링할 수 있습니다.

## 핵심 개념

### 다이어그램 구조

```yaml
version: light  # 필수: 형식 버전 식별자

# 선택: AI 에이전트 정의
persons:
  Agent Name:
    service: openai
    model: gpt-5-nano-2025-08-07
    api_key_id: APIKEY_XXXXX
    system_prompt: Optional system prompt

# 필수: 실행 노드 정의
nodes:
  - label: Node Label
    type: node_type
    position: {x: 100, y: 200}  # 시각적 위치
    props:
      # 노드별 속성

# 선택: 데이터 흐름 연결 정의
connections:
  - from: Source Node
    to: Target Node
    content_type: raw_text  # 데이터 변환 타입
    label: variable_name    # 타겟 노드에서의 변수명
```

### 필드 호환성과 매핑

DiPeO는 자동 필드 매핑을 통해 하위 호환을 보장합니다:

| 노드 타입        | 대체 필드                                                        | 비고                             |
| ------------ | ------------------------------------------------------------ | ------------------------------ |
| `code_job`   | `language` ⟷ `code_type`                                     | 상호 호환                          |
| `db`         | `file` ⟷ `source_details`                                    | 파일 경로 지정 시 둘 다 사용 가능           |
| `person_job` | 메모리 프로파일: `FULL`, `FOCUSED`, `MINIMAL`, `GOLDFISH`, `CUSTOM` | `CUSTOM`은 `memory_settings` 필요 |

이 매핑은 기존 다이어그램이 계속 동작하도록 하면서 최신 필드명을 지원합니다.

### 연결(Connections) 문법

DiPeO는 두 가지 동등한 YAML 문법을 지원합니다:

**전통적 멀티라인 형식:**

```yaml
connections:
  - from: Source Node
    to: Target Node
    content_type: raw_text
    label: variable_name
```

**콤팩트 단일 라인 형식:**

```yaml
connections:
  # 단순 연결
  - {from: Source Node, to: Target Node}
  
  # 추가 속성 포함
  - {from: Source Node, to: Target Node, content_type: raw_text, label: variable_name}
```

두 형식은 기능적으로 동일합니다. 콤팩트 형식은 다음에 유용합니다:

- 속성이 많지 않은 단순 연결
- 관련 연결을 시각적으로 뭉쳐 보기
- 대형 다이어그램에서 파일 길이 줄이기

### 노드 라벨과 참조

- 라벨은 다이어그램 내에서 고유해야 합니다.
- 라벨은 공백을 포함할 수 있습니다: `label: Data Processing Step`
- 중복 라벨은 자동 증가합니다: `Process` → `Process~1`
- `condition` 노드는 특수 핸들을 만듭니다: `Check Value_condtrue`, `Check Value_condfalse`

## 노드 타입 레퍼런스

### 1. START 노드

다이어그램 실행 진입점. 모든 다이어그램은 정확히 하나를 가져야 합니다.

```yaml
- label: Start
  type: start
  position: {x: 50, y: 200}
  props:
    trigger_mode: manual  # 또는 automatic
    custom_data:          # 선택: 초기 변수
      config:
        timeout: 30
        retries: 3
```

**핵심 기능:**

- `custom_data`는 모든 노드에 초기 변수를 제공합니다.
- 템플릿 문법으로 변수 접근 가능: `{{config.timeout}}`
- 수동 혹은 자동으로 트리거할 수 있습니다.

### 2. PERSON\_JOB 노드

LLM 에이전트로 프롬프트를 실행하며, 반복(iteration)과 메모리 관리를 지원합니다.

```yaml
- label: Analyzer
  type: person_job
  position: {x: 400, y: 200}
  props:
    person: Agent Name              # persons 섹션 참조
    default_prompt: 'Analyze {{data}}'
    first_only_prompt: 'Start analysis of {{data}}'  # 최초 반복에서만 사용
    prompt_file: code-review.txt    # /files/prompts/에서 로드(선택)
    max_iteration: 5
    memory_profile: FOCUSED         # 메모리 관리 전략
    tools:                          # 선택: LLM 도구
      - type: web_search_preview
        enabled: true
    memory_settings:                # (CUSTOM 프로파일 시) 고급 메모리 제어
      view: conversation_pairs       # 옵션: all_involved, sent_by_me, sent_to_me,
                                     # system_and_me, conversation_pairs, all_messages
      max_messages: 20
      preserve_system: true
```

**메모리 프로파일:**

- `FULL`: 대화 전체 이력
- `FOCUSED`: 최근 대화 쌍 20개(분석 기본값)
- `MINIMAL`: 시스템 + 최근 5개 메시지
- `GOLDFISH`: 마지막 2개 메시지만, 시스템 미보존
- `CUSTOM`: `memory_settings`로 사용자 정의

**프롬프트 템플릿:**

- `first_only_prompt`: 최초 반복에만 사용
- `default_prompt`: 이후 모든 반복에서 사용
- `prompt_file`: `/files/prompts/` 디렉터리의 외부 프롬프트 파일 경로(파일명만)
- 핸들바 문법 지원: `{{variable}}`, `{{nested.property}}`

**외부 프롬프트 파일 사용:**

- 파일은 `/files/prompts/`에 위치해야 합니다.
- 전체 경로가 아닌 파일명만 사용(예: `code-review.txt`)
- 활용처: 여러 다이어그램 간 프롬프트 재사용, 장문 프롬프트 관리, 별도 버전 관리
- `prompt_file`과 인라인 프롬프트가 동시에 있으면 외부 파일이 우선합니다.

### 3. CODE\_JOB 노드

여러 언어로 코드를 실행하며 입력 변수를 그대로 사용할 수 있습니다.

#### 인라인 코드

```yaml
- label: Transform Data
  type: code_job
  position: {x: 400, y: 200}
  props:
    language: python  # python, typescript, bash, shell
    code: |
      # 연결 라벨로 들어온 입력 변수 사용
      raw = raw_data  # 'raw_data' 라벨에서 전달됨
      config = processing_config
      
      # 데이터 처리
      processed = {
          'total': len(raw),
          'valid': sum(1 for r in raw if r.get('valid')),
          'transformed': [transform(r) for r in raw]
      }
      
      # 'result' 변수 또는 return으로 출력
      result = processed
      # OR: return processed
```

#### 외부 코드(복잡 로직 권장)

```yaml
# 방법 1: filePath 속성 사용
- label: Process Complex Data
  type: code_job
  position: {x: 400, y: 200}
  props:
    language: python
    filePath: files/code/data_processor.py
    functionName: process_data

# 방법 2: code 속성에 파일 경로 사용
- label: Process Data Alternative
  type: code_job
  position: {x: 400, y: 200}
  props:
    code_type: python  # 주의: code_type 또는 language 모두 가능
    code: files/code/data_processor.py  # code 필드에 파일 경로
    functionName: process_data
```

**외부 코드 관련 중요 사항:**

- `code`에는 인라인 코드 또는 파일 경로 둘 다 올 수 있습니다.
- `code`가 파일 확장자로 경로로 인식되면 외부 코드로 처리됩니다.
- `filePath`와 파일 경로가 있는 `code`는 동일한 효과를 냅니다.
- 외부 파일 사용 시 `functionName`이 필요합니다.
- 언어 지정은 `code_type` 또는 `language`로 상호 호환됩니다.

**외부 파일 구조 예:**

```python
# files/code/data_processor.py
def process_data(raw_data, config, **kwargs):
    """
    함수는 모든 입력 변수를 키워드 인자로 받습니다.
    함수명은 노드의 'functionName'과 일치해야 합니다.
    모든 연결 변수는 키워드 인자로 전달됩니다.
    """
    # 처리 로직
    result = transform(raw_data, config)
    return result  # 반환값이 노드 출력이 됩니다

# 같은 파일에 여러 함수도 가능

def validate_data(raw_data, **kwargs):
    """functionName: validate_data로 호출 가능"""
    return {"valid": True, "data": raw_data}
```

**언어 지원:**

- **Python**: Python 3.13+ 및 async 지원
- **TypeScript**: Node.js 런타임 + TS 컴파일
- **Bash/Shell**: 시스템 명령(적절한 이스케이프 포함)

**속성명:**

- 언어 지정 시 `language`와 `code_type`을 상호 교환적으로 사용할 수 있습니다.

**중요 메모:**

- 연결 라벨로 전달된 변수는 동일한 이름으로 접근합니다.
- `result =` 또는 `return`으로 다음 노드에 데이터 전달
- 외부 파일 경로는 프로젝트 루트 기준
- 함수는 모든 입력을 키워드 인자로 받습니다.

### 4. CONDITION 노드

불리언 표현식 또는 내장 조건에 따라 흐름을 제어합니다.

```yaml
# 내장 조건 사용
- label: Check Iterations
  type: condition
  position: {x: 600, y: 400}
  props:
    condition_type: detect_max_iterations  # 모든 person_job이 max에 도달했는가?
    flipped: true  # true/false 출력을 반전

# 사용자 정의 표현식
- label: Validate Quality
  type: condition
  position: {x: 600, y: 400}
  props:
    condition_type: custom
    expression: score >= 70 and len(errors) == 0
```

**내장 조건:**

- `detect_max_iterations`: 모든 `person_job` 노드가 `max_iteration`에 도달하면 true
- `nodes_executed`: 특정 노드의 실행 여부 확인
- `custom`: 모든 변수에 접근 가능한 Python 표현식 평가

**연결 핸들:**

- `NodeLabel_condtrue`: 조건이 참일 때
- `NodeLabel_condfalse`: 조건이 거짓일 때

### 5. DB 노드

파일 시스템에서 데이터 읽기/쓰기 작업을 수행합니다.

```yaml
# 단일 파일 읽기
- label: Load Config
  type: db
  position: {x: 200, y: 200}
  props:
    operation: read
    sub_type: file
    source_details: files/config/settings.json  # 내부적으로 'file'과 매핑

# 여러 파일 읽기
- label: Load All Configs
  type: db
  position: {x: 200, y: 200}
  props:
    operation: read
    sub_type: file
    source_details:
      - files/config/main.json
      - files/config/override.json
      - files/config/secrets.json

# 대체 문법: 'file' 속성 사용(둘 다 동작)
- label: Load Config Alt
  type: db
  position: {x: 200, y: 250}
  props:
    operation: read
    sub_type: file
    file: files/config/settings.json

# 글롭 패턴으로 파일 읽기
- label: Load JSON Files with Glob
  type: db
  position: {x: 200, y: 300}
  props:
    operation: read
    sub_type: file
    serialize_json: true  # JSON 자동 파싱
    glob: true            # 글롭 패턴 확장
    source_details:
      - "temp/*.json"         # temp/의 모든 JSON
      - "config/*.yaml"       # config/의 모든 YAML
      - "logs/2025-*.log"     # 날짜 패턴 로그
      - "temp/**/*.csv"       # 재귀 CSV
```

**메모:** `source_details`와 `file` 속성은 상호 호환되며, 내부에서 매핑됩니다.

**글롭 패턴 지원:**

- `glob: true`로 패턴 확장 활성화
- `*`(임의 문자열), `?`(단일 문자), `[abc]`(문자 집합) 지원
- `glob: true`가 아니면 패턴은 리터럴 파일명으로 처리
- 코드 생성에서 동적 파일 검색에 유용

**출력:**

- 단일 파일: 문자열로 내용 반환
- 여러 파일: `{경로: 내용}` 딕셔너리 반환
- 글롭: 모든 매칭을 확장하여 딕셔너리로 반환
- JSON 파일은 `serialize_json: true`를 설정해야 자동 파싱됩니다.

### 6. ENDPOINT 노드

결과를 파일로 저장하며 포맷 변환을 지원합니다.

```yaml
- label: Save Report
  type: endpoint
  position: {x: 800, y: 200}
  props:
    file_format: md      # txt, json, yaml, md
    save_to_file: true
    file_path: files/results/report.md  # 프로젝트 루트 기준
```

**포맷 처리:**

- `json`: 객체를 JSON으로 직렬화
- `yaml`: YAML로 변환
- `txt`/`md`: 텍스트를 그대로 저장

### 7. API\_JOB 노드

템플릿을 지원하는 HTTP 요청을 수행합니다.

```yaml
- label: Fetch Exchange Rates
  type: api_job
  position: {x: 400, y: 200}
  props:
    url: https://api.example.com/{{endpoint}}
    method: POST  # GET, POST, PUT, DELETE
    headers:
      Authorization: Bearer {{api_token}}
      Content-Type: application/json
    body:
      currency: USD
      amount: {{amount}}
    timeout: 30
```

**특징:**

- URL, 헤더, 바디에 템플릿 변수 사용 가능
- 바디는 자동으로 JSON 직렬화
- 응답은 텍스트로 다운스트림 노드에 전달

### 8. SUB\_DIAGRAM 노드

다른 다이어그램을 노드처럼 실행하여 모듈형 구성을 가능케 합니다.

```yaml
# 단일 실행
- label: Process Batch
  type: sub_diagram
  position: {x: 400, y: 200}  
  props:
    diagram_name: workflows/data_processor
    diagram_format: light
    passInputData: true  # 모든 입력을 서브 다이어그램으로 전달

# 배치 실행
- label: Process Items
  type: sub_diagram
  position: {x: 400, y: 200}
  props:
    diagram_name: workflows/process_single_item
    diagram_format: light
    batch: true
    batch_input_key: items  # 배열 변수 키
    batch_parallel: true    # 병렬 실행
```

**주요 속성:**

- `passInputData`: 현재 변수 전체를 서브 다이어그램으로 전달
- `batch`: 배열 항목마다 한 번씩 실행
- `batch_parallel`: 배치 항목을 동시 실행
- `ignoreIfSub`: 이미 서브로 실행 중이면 건너뜀

### 9. TEMPLATE\_JOB 노드

Jinja2 기반의 고급 템플릿 렌더링.

```yaml
- label: Generate Code
  type: template_job
  position: {x: 600, y: 300}
  props:
    engine: jinja2
    template_path: files/templates/model.j2
    output_path: generated/model.py
    variables:
      models: "{{extracted_models}}"
      config: "{{generation_config}}"
```

**특징:**

- Jinja2 전체 문법 지원
- 사용자 정의 필터(ts\_to\_python, snake\_case 등)
- 파일로 직접 출력
- 업스트림 변수 전체 접근 가능

### 10. USER\_RESPONSE 노드

실행 중 사용자 입력을 받습니다.

```yaml
- label: Get Confirmation
  type: user_response
  position: {x: 400, y: 200}
  props:
    prompt: 'Review the results and confirm (yes/no):'
    timeout: 300  # 5분
    validation_type: text  # 또는 number, boolean
```

### 11. HOOK 노드

셸 명령, 웹훅, 파이썬 스크립트, 파일 작업 등 외부 훅을 실행합니다.

```yaml
# 셸 명령 훅
- label: Run Script
  type: hook
  position: {x: 400, y: 200}
  props:
    hook_type: shell
    config:
      command: "python scripts/process.py {{input_file}}"
      timeout: 60

# 웹훅 훅
- label: Send Notification
  type: hook
  position: {x: 400, y: 300}
  props:
    hook_type: webhook
    config:
      url: "https://hooks.slack.com/services/xxx"
      method: POST
      headers:
        Content-Type: application/json
      body:
        text: "Processing completed for {{task_id}}"

# 파이썬 스크립트 훅
- label: Custom Processing
  type: hook
  position: {x: 400, y: 400}
  props:
    hook_type: python
    config:
      script: "scripts/custom_processor.py"
      function: "process_data"
      args:
        data: "{{input_data}}"
```

### 12. INTEGRATED\_API 노드

Notion, Slack, GitHub 등 다양한 API 제공자 작업을 수행합니다.

```yaml
- label: Create Notion Page
  type: integrated_api
  position: {x: 400, y: 200}
  props:
    provider: notion
    operation: create_page
    config:
      database_id: "{{notion_database_id}}"
      properties:
        title: "{{page_title}}"
        status: "In Progress"
    api_key_id: APIKEY_NOTION_XXX

- label: Send Slack Message
  type: integrated_api
  position: {x: 400, y: 300}
  props:
    provider: slack
    operation: post_message
    config:
      channel: "#general"
      text: "Build completed: {{build_status}}"
    api_key_id: APIKEY_SLACK_XXX
```

### 13. JSON\_SCHEMA\_VALIDATOR 노드

JSON 데이터를 스키마로 검증합니다.

```yaml
- label: Validate Config
  type: json_schema_validator
  position: {x: 400, y: 200}
  props:
    schema:
      type: object
      properties:
        name:
          type: string
        age:
          type: number
          minimum: 0
      required: ["name", "age"]
    strict: true  # 검증 오류 시 실패
```

### 14. TYPESCRIPT\_AST 노드

TypeScript 코드를 AST로 파싱/분석합니다.

```yaml
- label: Parse TypeScript
  type: typescript_ast
  position: {x: 400, y: 200}
  props:
    source_file: "src/components/Button.tsx"
    extract:
      - interfaces
      - functions
      - exports
```

### 15. PERSON\_BATCH\_JOB 노드

동일한 person 설정으로 여러 항목을 배치 처리합니다.

```yaml
- label: Batch Analysis
  type: person_batch_job
  position: {x: 400, y: 200}
  props:
    person: Analyst
    batch_input_key: items
    batch_parallel: true
    default_prompt: "Analyze this item: {{item}}"
    max_iteration: 1
```

## 데이터 흐름과 변수 해석

### 연결 라벨은 핵심입니다

연결 라벨은 타겟 노드에서의 변수명을 정의합니다:

```yaml
connections:
  # 라벨이 없으면 데이터는 흐르지만 이름으로 접근할 수 없습니다
  - from: Load Data
    to: Process
    
  # 라벨이 있으면 Process 노드에 'raw_data' 변수가 생성됩니다
  - from: Load Data
    to: Process
    label: raw_data
    
  # 서로 다른 이름으로 다중 입력
  - from: Load Config
    to: Process
    label: config
    
  # Process 노드에서의 접근:
  # Python: raw_data, config
  # 템플릿: {{raw_data}}, {{config}}
```

### 콘텐츠 타입

노드 간 데이터 변환 방식을 제어합니다:

```yaml
# 기본: 단순 텍스트
- from: Source
  to: Target
  content_type: raw_text
  
# person_job 간 전체 대화 상태 전달
- from: Agent 1
  to: Agent 2
  content_type: conversation_state
  
# 코드 실행 결과의 구조화된 데이터
- from: Code Job
  to: Person Job
  content_type: object
```

### 변수 스코프와 전파

1. **Start 노드 변수**: `custom_data`를 통해 전역으로 제공
2. **연결 변수**: 타겟 노드에 스코프됨
3. **코드 변수**: `result` 또는 반환값이 전파됨
4. **템플릿 변수**: 모든 업스트림 변수에 접근 가능

## 고급 패턴

### 1. 조건을 통한 반복 처리

```yaml
nodes:
  - label: Initialize Counter
    type: code_job
    props:
      code: |
        counter = 0
        max_retries = 5
        items_to_process = load_items()
        result = {"counter": counter, "items": items_to_process}
        
  - label: Process Item
    type: code_job
    props:
      code: |
        current = state["items"][state["counter"]]
        processed = process_item(current)
        state["counter"] += 1
        result = state
        
  - label: Check Complete
    type: condition
    props:
      condition_type: custom
      expression: state["counter"] >= len(state["items"])
      
connections:
  - from: Initialize Counter
    to: Process Item
    label: state
  - from: Process Item
    to: Check Complete
    label: state
  - from: Check Complete_condfalse
    to: Process Item
    label: state  # 루프백
  - from: Check Complete_condtrue
    to: Save Results
```

### 2. 멀티 에이전트 토론 패턴

```yaml
persons:
  Proposer:
    service: openai
    model: gpt-5-nano-2025-08-07
    system_prompt: You propose innovative solutions
    
  Critic:
    service: openai
    model: gpt-5-nano-2025-08-07
    system_prompt: You critically evaluate proposals
    
  Synthesizer:
    service: openai
    model: gpt-5-nano-2025-08-07
    system_prompt: You synthesize different viewpoints

nodes:
  - label: Initial Proposal
    type: person_job
    props:
      person: Proposer
      first_only_prompt: 'Propose a solution for: {{problem}}'
      default_prompt: 'Refine your proposal based on criticism'
      max_iteration: 3
      memory_profile: FOCUSED
      
  - label: Critical Review
    type: person_job
    props:
      person: Critic
      default_prompt: |
        Evaluate this proposal:
        {{proposal}}
        
        Identify strengths and weaknesses.
      max_iteration: 3
      memory_profile: GOLDFISH  # 매 반복 신선한 관점
      
  - label: Synthesize
    type: person_job
    props:
      person: Synthesizer
      default_prompt: |
        Given the proposal and criticism:
        Proposal: {{proposal}}
        Criticism: {{criticism}}
        
        Create a balanced synthesis.
      max_iteration: 1
      memory_profile: FULL
```

### 3. 에러 처리와 재시도 로직

```yaml
nodes:
  - label: API Call
    type: api_job
    props:
      url: https://api.example.com/data
      timeout: 10
      
  - label: Check Response
    type: code_job
    props:
      code: |
        try:
            data = json.loads(api_response)
            if data.get("status") == "success":
                result = {"success": True, "data": data}
            else:
                result = {"success": False, "error": data.get("error")}
        except:
            result = {"success": False, "error": "Invalid response"}
            
  - label: Should Retry
    type: condition
    props:
      condition_type: custom
      expression: not response["success"] and retry_count < 3
      
  - label: Increment Retry
    type: code_job
    props:
      code: |
        retry_count = retry_count + 1
        wait_time = 2 ** retry_count  # 지수 백오프
        time.sleep(wait_time)
        result = retry_count
```

### 4. 동적 배치 처리

```yaml
nodes:
  - label: Load Items
    type: db
    props:
      operation: read
      sub_type: file
      source_details: files/data/items.json
      
  - label: Parse Items
    type: code_job
    props:
      code: |
        items = json.loads(raw_json)
        # 서브 다이어그램 배치를 위한 구조 생성
        result = {
            "items": [{"id": i, "data": item} for i, item in enumerate(items)]
        }
        
  - label: Process Batch
    type: sub_diagram
    props:
      diagram_name: workflows/process_single
      diagram_format: light
      batch: true
      batch_input_key: items
      batch_parallel: true  # 모든 항목 병렬 처리
      
  - label: Aggregate Results
    type: code_job
    props:
      code: |
        # batch_results: 각 실행의 출력 배열
        successful = [r for r in batch_results if r.get("status") == "success"]
        failed = [r for r in batch_results if r.get("status") != "success"]
        
        result = {
            "total": len(batch_results),
            "successful": len(successful),
            "failed": len(failed),
            "results": successful
        }
```

## 서브 다이어그램과 모듈 조합

### 기본 서브 다이어그램 사용

```yaml
# 부모 다이어그램
nodes:
  - label: Prepare Data
    type: code_job
    props:
      code: |
        result = {
            "input_file": "data.csv",
            "config": {"quality_threshold": 80}
        }
        
  - label: Run Processor
    type: sub_diagram
    props:
      diagram_name: processors/data_quality_check
      diagram_format: light
      passInputData: true  # 모든 변수를 서브 다이어그램으로 전달
```

### 서브 다이어그램으로 배치 처리

```yaml
# 부모 다이어그램 - 여러 파일 처리
nodes:
  - label: List Files
    type: code_job
    props:
      code: |
        import glob
        files = glob.glob("files/input/*.csv")
        result = {"items": [{"file_path": f} for f in files]}
        
  - label: Process Files
    type: sub_diagram
    props:
      diagram_name: processors/single_file_processor
      diagram_format: light
      batch: true
      batch_input_key: items
      batch_parallel: true
```

### 조건부 서브 다이어그램 실행

```yaml
nodes:
  - label: Check Environment
    type: code_job
    props:
      code: |
        env = os.environ.get("ENVIRONMENT", "dev")
        result = {"env": env, "is_production": env == "prod"}
        
  - label: Is Production
    type: condition
    props:
      condition_type: custom
      expression: is_production
      
  - label: Run Production Pipeline
    type: sub_diagram
    props:
      diagram_name: pipelines/production
      diagram_format: light
      passInputData: true
      
  - label: Run Dev Pipeline
    type: sub_diagram
    props:
      diagram_name: pipelines/development
      diagram_format: light
      passInputData: true
      
connections:
  - from: Is Production_condtrue
    to: Run Production Pipeline
  - from: Is Production_condfalse
    to: Run Dev Pipeline
```

## 에러 처리와 복원력

### 1. 점진적 기능 저하(Graceful Degradation)

```yaml
nodes:
  - label: Primary API
    type: api_job
    props:
      url: https://primary.api.com/data
      timeout: 5
      
  - label: Check Primary
    type: code_job
    props:
      code: |
        try:
            data = json.loads(primary_response)
            result = {"success": True, "data": data, "source": "primary"}
        except:
            result = {"success": False, "source": "primary"}
            
  - label: Primary Failed
    type: condition
    props:
      condition_type: custom
      expression: not api_result["success"]
      
  - label: Fallback API
    type: api_job
    props:
      url: https://fallback.api.com/data
      timeout: 10
      
connections:
  - from: Primary Failed_condtrue
    to: Fallback API
  - from: Primary Failed_condfalse
    to: Process Data
```

### 2. 검증과 오류 수집

```yaml
nodes:
  - label: Validate Input
    type: code_job
    props:
      code: |
        errors = []
        warnings = []
        
        # 검증 로직
        if not data.get("required_field"):
            errors.append("Missing required_field")
            
        if len(data.get("items", [])) > 1000:
            warnings.append("Large dataset may take time")
            
        result = {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "data": data
        }
        
  - label: Is Valid
    type: condition
    props:
      condition_type: custom
      expression: validation["valid"]
      
  - label: Log Errors
    type: endpoint
    props:
      file_format: json
      file_path: files/logs/validation_errors.json
```

### 3. 타임아웃과 서킷 브레이커 패턴

```yaml
nodes:
  - label: Check Circuit State
    type: code_job
    props:
      code: |
        # 서킷 브레이커 상태 로드
        try:
            with open("temp/circuit_state.json", "r") as f:
                state = json.load(f)
        except:
            state = {"failures": 0, "last_failure": 0}
            
        # 회로 개방 여부 확인
        now = time.time()
        if state["failures"] >= 3:
            if now - state["last_failure"] < 300:  # 5분 쿨다운
                result = {"circuit_open": True}
            else:
                # 회로 리셋
                state["failures"] = 0
                result = {"circuit_open": False, "state": state}
        else:
            result = {"circuit_open": False, "state": state}
```

## 성능 최적화

### 1. 병렬 실행 전략

```yaml
# 병렬 데이터 패치
nodes:
  - label: Start Parallel Fetch
    type: code_job
    props:
      code: |
        sources = [
            {"id": "users", "url": "/api/users"},
            {"id": "products", "url": "/api/products"},
            {"id": "orders", "url": "/api/orders"}
        ]
        result = {"items": sources}
        
  - label: Fetch Data
    type: sub_diagram
    props:
      diagram_name: utilities/fetch_single_source
      batch: true
      batch_input_key: items
      batch_parallel: true  # 모든 소스를 동시에 가져오기
```

### 2. 캐싱 전략

```yaml
nodes:
  - label: Check Cache
    type: code_job
    props:
      code: |
        import hashlib
        import os
        
        # 캐시 키 생성
        cache_key = hashlib.md5(json.dumps(params).encode()).hexdigest()
        cache_file = f"temp/cache/{cache_key}.json"
        
        if os.path.exists(cache_file):
            # 캐시 연령 확인
            age = time.time() - os.path.getmtime(cache_file)
            if age < 3600:  # 1시간 캐시
                with open(cache_file, "r") as f:
                    cached_data = json.load(f)
                result = {"hit": True, "data": cached_data}
            else:
                result = {"hit": False, "cache_file": cache_file}
        else:
            result = {"hit": False, "cache_file": cache_file}
```

### 3. 배치 vs 순차 처리

```yaml
# 데이터 규모에 따른 전략 선택
nodes:
  - label: Analyze Workload
    type: code_job
    props:
      code: |
        item_count = len(items)
        avg_size = sum(len(str(item)) for item in items) / item_count
        
        # 대규모면 배치, 소규모면 순차
        use_batch = item_count > 100 or avg_size > 1000
        
        result = {
            "use_batch": use_batch,
            "items": items,
            "stats": {
                "count": item_count,
                "avg_size": avg_size
            }
        }
        
  - label: Should Batch
    type: condition
    props:
      condition_type: custom
      expression: use_batch
```

## 모범 사례

### 1. 노드 구성

- **관련 노드를 시각적으로 그룹화**: x 좌표로 흐름 진행을 표현
- **설명적인 라벨 사용**: `Validate User Input`처럼 명확하게
- **일관된 배치**: 가독성을 위해 x를 200\~400씩 증가
- **핸들 방향**: 레이아웃을 깔끔히 하려면 `flipped` 속성 활용

### 2. 변수 네이밍

```yaml
connections:
  # 좋은 예: 의미가 분명
  - from: Load User Data
    to: Process Users
    label: user_records
    
  # 나쁜 예: 모호함
  - from: Node1
    to: Node2
    label: data
```

### 3. 외부 코드 구성

**외부 파일을 사용할 때:**

- 10\~15줄을 넘는 코드
- 여러 다이어그램에서 재사용되는 함수
- import와 헬퍼가 필요한 복잡 로직
- 독립 테스트가 필요한 코드
- DiPeO 코드젠 패턴(모든 코드를 외부 파일)에 따를 때

**디렉터리 구조 예:**

```
files/
├── code/
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── user_validator.py
│   │   └── data_validator.py
│   ├── processors/
│   │   ├── __init__.py
│   │   └── data_processor.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── codegen/
│   └── code/
│       ├── models/
│       │   └── generate_python_models/
│       │       └── python_models_extractor_v2.py
│       └── shared/
│           └── parse_node_data/
│               └── parser_functions.py
```

**인라인 vs 외부 코드 예:**

```yaml
# 인라인 - 단순 작업에 적합
- label: Simple Transform
  type: code_job
  props:
    code: |
      result = input_data.upper()

# 외부 - 복잡 로직에 적합
- label: Complex Processing
  type: code_job
  props:
    code: files/code/processors/data_processor.py
    functionName: process_complex_data
    # 또는 filePath 사용:
    # filePath: files/code/processors/data_processor.py
```

### 4. 오류 메시지와 로깅

```yaml
- label: Process with Logging
  type: code_job
  props:
    code: |
      import logging
      log = logging.getLogger(__name__)
      
      try:
          log.info(f"Processing {len(items)} items")
          processed = process_items(items)
          log.info(f"Successfully processed {len(processed)} items")
          result = {"success": True, "data": processed}
      except Exception as e:
          log.error(f"Processing failed: {str(e)}")
          result = {"success": False, "error": str(e)}
```

### 5. 다이어그램 테스트

```yaml
# 테스트 하니스 다이어그램
nodes:
  - label: Load Test Cases
    type: db
    props:
      source_details: files/tests/test_cases.json
      
  - label: Run Tests
    type: sub_diagram
    props:
      diagram_name: main_workflow
      batch: true
      batch_input_key: test_cases
      
  - label: Validate Results
    type: code_job
    props:
      code: |
        failures = []
        for i, (result, expected) in enumerate(zip(results, test_cases)):
            if not validate_result(result, expected):
                failures.append({
                    "test": i,
                    "expected": expected,
                    "actual": result
                })
        
        if failures:
            raise AssertionError(f"{len(failures)} tests failed")
```

## 프로덕션 패턴

### 1. 구성(Config) 관리

```yaml
nodes:
  - label: Load Environment Config
    type: code_job
    props:
      code: |
        env = os.environ.get("ENVIRONMENT", "dev")
        config_file = f"files/config/{env}.json"
        
        with open(config_file, "r") as f:
            config = json.load(f)
            
        # 환경 변수와 병합
        for key, value in os.environ.items():
            if key.startswith("APP_"):
                config[key[4:].lower()] = value
                
        result = config
```

### 2. 모니터링과 메트릭

```yaml
nodes:
  - label: Start Timer
    type: code_job
    props:
      code: |
        import time
        start_time = time.time()
        result = {"start_time": start_time}
        
  - label: Record Metrics
    type: code_job
    props:
      code: |
        duration = time.time() - timing["start_time"]
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "items_processed": len(results),
            "success_rate": sum(1 for r in results if r["success"]) / len(results),
            "errors": [r["error"] for r in results if not r["success"]]
        }
        
        # 모니터링 시스템으로 전송
        send_metrics(metrics)
        result = metrics
```

### 3. 정상 종료(Graceful Shutdown)

```yaml
nodes:
  - label: Check Shutdown Signal
    type: code_job
    props:
      code: |
        import signal
        
        shutdown_requested = False
        
        def handle_shutdown(signum, frame):
            global shutdown_requested
            shutdown_requested = True
            
        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)
        
        result = {"shutdown": shutdown_requested}
        
  - label: Should Continue
    type: condition
    props:
      condition_type: custom
      expression: not status["shutdown"] and current_item < total_items
```

### 4. 배포 패턴

```yaml
# 블루-그린 배포 확인기
nodes:
  - label: Check Current Version
    type: api_job
    props:
      url: https://api.myapp.com/version
      
  - label: Compare Versions
    type: code_job
    props:
      code: |
        current = json.loads(version_response)["version"]
        target = os.environ.get("TARGET_VERSION")
        
        if current == target:
            result = {"deploy": False, "reason": "Already at target version"}
        else:
            result = {"deploy": True, "current": current, "target": target}
```

## 디버깅과 트러블슈팅

### 1. 디버그 모드 실행

```bash
# 디버그 출력과 함께 실행
dipeo run my_diagram --light --debug

# 장시간 실행 타임아웃
dipeo run my_diagram --light --debug --timeout=300

# 초기 데이터 지정
dipeo run my_diagram --light --debug --input-data '{"user_id": 123}'
```

### 2. 노드 디버깅

```yaml
- label: Debug State
  type: code_job
  props:
    code: |
      # 사용 가능한 모든 변수 출력
      print("=== Debug State ===")
      for key, value in locals().items():
          if not key.startswith("_"):
              print(f"{key}: {type(value)} = {repr(value)[:100]}")
      
      # 데이터 패스스루
      result = input_data
```

### 3. 실행 모니터링

```yaml
# 모니터링 노드 추가
- label: Log Execution
  type: code_job
  props:
    code: |
      with open("files/logs/execution.log", "a") as f:
          f.write(f"{datetime.now()}: Node {node_label} executed\n")
          f.write(f"  Input: {json.dumps(input_data)[:200]}\n")
      result = input_data
```

### 4. 흔한 이슈와 해결책

**이슈: 템플릿에서 변수를 찾을 수 없음**

```yaml
# 문제
default_prompt: "Process {{data}}"  # 'data' 미정의

# 해결: 연결에 라벨을 지정
connections:
  - from: Source
    to: Target
    label: data  # 'data' 변수를 생성
```

**이슈: 서브 다이어그램이 입력을 받지 못함**

```yaml
# 문제
props:
  diagram_name: sub_workflow
  passInputData: false  # 입력 전달 안 함

# 해결
props:
  diagram_name: sub_workflow
  passInputData: true  # 모든 변수 전달
```

**이슈: 조건이 항상 false**

```yaml
# 문제
condition_type: custom
expression: score > 80  # 'score'가 문자열일 수 있음

# 해결
expression: float(score) > 80  # 명시적 형 변환
```

### 5. 성능 프로파일링

```yaml
nodes:
  - label: Profile Section
    type: code_job
    props:
      code: |
        import cProfile
        import pstats
        import io
        
        pr = cProfile.Profile()
        pr.enable()
        
        # 비용이 큰 연산
        result = expensive_function(input_data)
        
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(10)  # 상위 10개 함수
        
        with open("files/logs/profile.txt", "w") as f:
            f.write(s.getvalue())
```

## 결론

DiPeO Light 형식은 복잡한 워크플로를 읽기 쉬운 형태로 구성하는 강력한 방법을 제공합니다. 본 가이드의 노드 타입, 데이터 흐름 패턴, 모범 사례를 이해하면 효율적이고 유지보수 가능한 프로덕션급 다이어그램을 만들 수 있습니다.

핵심 요약:

1. **항상 연결에 라벨을 지정**하여 변수 접근을 보장한다.
2. **복잡 로직은 외부 코드 파일**로 관리한다.
3. **서브 다이어그램을 활용**해 모듈성을 높인다.
4. **조건/검증으로 오류를 계획**하고 다룬다.
5. **디버그/로깅으로 실행을 모니터링**한다.
6. **다양한 입력 시나리오로 철저히 테스트**한다.

