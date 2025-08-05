# DiPeO Light 다이어그램 종합 가이드

## 목차

1. [소개](#소개)
2. [핵심 개념](#핵심-개념)
3. [노드 타입 레퍼런스](#노드-타입-레퍼런스)
4. [데이터 흐름과 변수 해석](#데이터-흐름과-변수-해석)
5. [고급 패턴](#고급-패턴)
6. [서브 다이어그램과 모듈식 구성](#서브-다이어그램과-모듈식-구성)
7. [오류 처리와 복원력](#오류-처리와-복원력)
8. [성능 최적화](#성능-최적화)
9. [모범 사례](#모범-사례)
10. [프로덕션 패턴](#프로덕션-패턴)
11. [디버깅과 문제 해결](#디버깅과-문제-해결)

## 소개

DiPeO Light 포맷은 실행 가능한 다이어그램을 만들기 위한 사람이 읽을 수 있는 YAML 구문입니다. 빠른 프로토타이핑, 복잡한 오케스트레이션, 그리고 프로덕션 워크플로우를 위해 설계되었습니다. 이 가이드는 기본 개념부터 DiPeO의 자체 코드 생성 시스템에서 사용되는 고급 패턴까지 모든 것을 다룹니다.

### 핵심 원칙

1. **레이블 기반 식별**: 노드는 UUID 대신 사람이 읽을 수 있는 레이블로 식별됩니다
2. **명시적 데이터 흐름**: 연결 레이블이 다운스트림 노드의 변수 이름을 정의합니다
3. **타입 안전성**: 각 노드 타입은 특정 속성과 검증을 가집니다
4. **구성 가능성**: 다이어그램은 서브 다이어그램을 통해 중첩되고 구성될 수 있습니다
5. **시각적 실행**: 모든 다이어그램은 실시간으로 시각화되고 모니터링될 수 있습니다

## 핵심 개념

### 다이어그램 구조

```yaml
version: light  # 필수 버전 식별자

# 선택사항: AI 에이전트 정의
persons:
  Agent Name:
    service: openai
    model: gpt-4.1-nano
    api_key_id: APIKEY_XXXXX
    system_prompt: 선택적 시스템 프롬프트

# 필수: 실행 노드 정의
nodes:
  - label: Node Label
    type: node_type
    position: {x: 100, y: 200}  # 시각적 위치
    props:
      # 노드별 속성

# 선택사항: 데이터 흐름 연결 정의
connections:
  - from: Source Node
    to: Target Node
    content_type: raw_text  # 데이터 변환 타입
    label: variable_name    # 대상 노드의 변수 이름
```

### 노드 레이블과 참조

- 레이블은 다이어그램 내에서 고유해야 합니다
- 레이블에 공백 허용: `label: Data Processing Step`
- 중복 레이블은 자동 증가: `Process` → `Process~1`
- 조건 노드는 특별한 핸들 생성: `Check Value_condtrue`, `Check Value_condfalse`

## 노드 타입 레퍼런스

### 1. START 노드

다이어그램 실행의 진입점. 모든 다이어그램은 정확히 하나의 START 노드를 가져야 합니다.

```yaml
- label: Start
  type: start
  position: {x: 50, y: 200}
  props:
    trigger_mode: manual  # 또는 automatic
    custom_data:          # 선택사항: 초기 변수
      config:
        timeout: 30
        retries: 3
```

**주요 기능:**
- `custom_data`는 모든 노드에 초기 변수를 제공합니다
- 변수는 템플릿 구문으로 접근 가능: `{{config.timeout}}`
- 수동 또는 자동으로 트리거 가능

### 2. PERSON_JOB 노드

LLM 에이전트로 프롬프트를 실행하며, 반복과 메모리 관리를 지원합니다.

```yaml
- label: Analyzer
  type: person_job
  position: {x: 400, y: 200}
  props:
    person: Agent Name              # persons 섹션 참조
    default_prompt: 'Analyze {{data}}'
    first_only_prompt: 'Start analysis of {{data}}'  # 첫 번째 반복에만 사용
    max_iteration: 5
    memory_profile: FOCUSED         # 메모리 관리 전략
    tools:                          # 선택적 LLM 도구
      - type: web_search_preview
        enabled: true
    memory_settings:                # 고급 메모리 제어
      view: conversation_pairs
      max_messages: 20
      preserve_system: true
```

**메모리 프로파일:**
- `FULL`: 완전한 대화 기록
- `FOCUSED`: 최근 20개 대화 쌍 (분석의 기본값)
- `MINIMAL`: 시스템 + 최근 5개 메시지
- `GOLDFISH`: 마지막 2개 메시지만, 시스템 보존 안 함

**프롬프트 템플릿:**
- `first_only_prompt`: 첫 번째 반복에서만 사용
- `default_prompt`: 모든 후속 반복에 사용
- Handlebars 구문 지원: `{{variable}}`, `{{nested.property}}`

### 3. CODE_JOB 노드

입력 변수에 완전히 접근 가능한 여러 언어로 코드를 실행합니다.

#### 인라인 코드

```yaml
- label: Transform Data
  type: code_job
  position: {x: 400, y: 200}
  props:
    language: python  # python, typescript, bash, shell
    code: |
      # 연결에서 사용 가능한 입력 변수
      raw = raw_data  # 'raw_data' 레이블의 연결에서
      config = processing_config
      
      # 데이터 처리
      processed = {
          'total': len(raw),
          'valid': sum(1 for r in raw if r.get('valid')),
          'transformed': [transform(r) for r in raw]
      }
      
      # 'result' 변수 또는 return으로 출력
      result = processed
      # 또는: return processed
```

#### 외부 코드 (복잡한 로직에 권장)

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
    code_type: python  # 참고: code_type 또는 language 사용 가능
    code: files/code/data_processor.py  # code 필드에 파일 경로
    functionName: process_data
```

**외부 코드에 대한 중요 사항:**
- `code` 속성은 인라인 코드 또는 파일 경로를 포함할 수 있습니다
- `code`에 경로가 포함되면 (파일 확장자로 감지) 외부 코드로 처리됩니다
- `filePath`와 파일 경로가 있는 `code` 모두 같은 결과를 얻습니다
- 외부 파일 사용 시 `functionName`이 필요합니다
- 언어 지정에 `code_type` 또는 `language`를 상호 교환하여 사용

**외부 파일 구조:**
```python
# files/code/data_processor.py
def process_data(raw_data, config, **kwargs):
    """
    함수는 모든 입력 변수를 키워드 인수로 받습니다.
    함수 이름은 노드의 'functionName'과 일치해야 합니다.
    모든 연결 변수는 키워드 인수로 전달됩니다.
    """
    # 데이터 처리
    result = transform(raw_data, config)
    return result  # 반환 값이 노드 출력이 됩니다

# 같은 파일에 여러 함수를 가질 수 있습니다
def validate_data(raw_data, **kwargs):
    """functionName: validate_data로 호출할 수 있는 다른 함수"""
    return {"valid": True, "data": raw_data}
```

**언어 지원:**
- **Python**: 비동기 지원이 있는 전체 Python 3.13+
- **TypeScript**: TypeScript 컴파일이 있는 Node.js 런타임
- **Bash/Shell**: 적절한 이스케이핑이 있는 시스템 명령

**중요 사항:**
- 연결의 변수는 레이블 이름으로 사용 가능합니다
- 다음 노드에 데이터를 전달하려면 `result =` 또는 `return` 사용
- 외부 파일은 프로젝트 루트에 상대적입니다
- 함수는 모든 입력을 키워드 인수로 받습니다

### 4. CONDITION 노드

부울 표현식 또는 내장 조건에 따라 흐름을 제어합니다.

```yaml
# 내장 조건
- label: Check Iterations
  type: condition
  position: {x: 600, y: 400}
  props:
    condition_type: detect_max_iterations  # 모든 person_job이 최대값에 도달?
    flipped: true  # true/false 출력 반전

# 사용자 정의 표현식
- label: Validate Quality
  type: condition
  position: {x: 600, y: 400}
  props:
    condition_type: custom
    expression: score >= 70 and len(errors) == 0
```

**내장 조건:**
- `detect_max_iterations`: 모든 person_job 노드가 max_iteration에 도달하면 True
- `nodes_executed`: 특정 노드가 실행되었는지 확인
- `custom`: 모든 변수에 접근하여 Python 표현식 평가

**연결 핸들:**
- `NodeLabel_condtrue`: 조건이 true로 평가될 때
- `NodeLabel_condfalse`: 조건이 false로 평가될 때

### 5. DB 노드

데이터 읽기/쓰기를 위한 파일 시스템 작업.

```yaml
# 단일 파일 읽기
- label: Load Config
  type: db
  position: {x: 200, y: 200}
  props:
    operation: read
    sub_type: file
    source_details: files/config/settings.json

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

# glob 패턴으로 파일 읽기
- label: Load JSON Files with Glob
  type: db
  position: {x: 200, y: 300}
  props:
    operation: read
    sub_type: file
    serialize_json: true  # JSON 파일 자동 파싱
    glob: true            # glob 패턴 확장 활성화
    source_details:
      - "temp/*.json"         # temp/의 모든 JSON 파일
      - "config/*.yaml"       # config/의 모든 YAML 파일
      - "logs/2025-*.log"     # 날짜 패턴 로그
      - "temp/**/*.csv"       # 재귀적 CSV 파일
```

**Glob 패턴 지원:**
- 패턴 확장을 활성화하려면 `glob: true` 설정
- `*` (모든 문자), `?` (단일 문자), `[abc]` (문자 집합) 지원
- `glob: true` 없이는 패턴이 리터럴 파일명으로 처리됩니다
- 코드 생성에서 동적 파일 검색에 유용

**출력:**
- 단일 파일: 파일 내용을 문자열로 반환
- 여러 파일: 파일 경로를 키로, 내용을 값으로 하는 딕셔너리 반환
- Glob 패턴 (`glob: true`와 함께): 모든 일치하는 파일로 확장, 딕셔너리로 반환
- JSON 파일은 `serialize_json: true`가 설정되지 않으면 자동 파싱되지 않음

### 6. ENDPOINT 노드

형식 변환과 함께 결과를 파일에 저장합니다.

```yaml
- label: Save Report
  type: endpoint
  position: {x: 800, y: 200}
  props:
    file_format: md      # txt, json, yaml, md
    save_to_file: true
    file_path: files/results/report.md  # 프로젝트 루트에 상대적
```

**형식 처리:**
- `json`: 객체를 JSON으로 직렬화
- `yaml`: YAML 형식으로 변환
- `txt`/`md`: 텍스트 내용을 그대로 저장

### 7. API_JOB 노드

템플릿 지원이 있는 HTTP 요청.

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

**기능:**
- URL, 헤더, 본문의 템플릿 변수
- 본문의 자동 JSON 직렬화
- 응답은 다운스트림 노드에 텍스트로 사용 가능

### 8. SUB_DIAGRAM 노드

다른 다이어그램을 노드로 실행하여 모듈식 구성을 가능하게 합니다.

```yaml
# 단일 실행
- label: Process Batch
  type: sub_diagram
  position: {x: 400, y: 200}  
  props:
    diagram_name: workflows/data_processor
    diagram_format: light
    passInputData: true  # 모든 입력을 서브 다이어그램에 전달

# 배치 실행
- label: Process Items
  type: sub_diagram
  position: {x: 400, y: 200}
  props:
    diagram_name: workflows/process_single_item
    diagram_format: light
    batch: true
    batch_input_key: items  # 배치용 배열 변수
    batch_parallel: true    # 병렬로 실행
```

**주요 속성:**
- `passInputData`: 모든 현재 변수를 서브 다이어그램에 전달
- `batch`: 배열 항목당 한 번 실행
- `batch_parallel`: 배치 항목을 동시에 실행
- `ignoreIfSub`: 이미 서브 다이어그램으로 실행 중이면 건너뛰기

### 9. TEMPLATE_JOB 노드

Jinja2를 사용한 고급 템플릿 렌더링.

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

**기능:**
- 전체 Jinja2 구문 지원
- 사용자 정의 필터 (ts_to_python, snake_case 등)
- 직접 파일 출력
- 모든 업스트림 변수에 접근

### 10. USER_RESPONSE 노드

실행 중 대화형 사용자 입력.

```yaml
- label: Get Confirmation
  type: user_response
  position: {x: 400, y: 200}
  props:
    prompt: '결과를 검토하고 확인하세요 (yes/no):'
    timeout: 300  # 5분
    validation_type: text  # 또는 number, boolean
```

## 데이터 흐름과 변수 해석

### 연결 레이블이 중요합니다

연결 레이블은 대상 노드의 변수 이름을 정의합니다:

```yaml
connections:
  # 레이블 없이 - 데이터는 흐르지만 이름으로 접근할 수 없음
  - from: Load Data
    to: Process
    
  # 레이블과 함께 - Process 노드에 'raw_data' 변수 생성
  - from: Load Data
    to: Process
    label: raw_data
    
  # 다른 이름의 여러 입력
  - from: Load Config
    to: Process
    label: config
    
  # Process 노드에서 접근:
  # Python: raw_data, config
  # 템플릿: {{raw_data}}, {{config}}
```

### 콘텐츠 타입

노드 간 데이터 변환 제어:

```yaml
# 일반 텍스트 출력 (기본값)
- from: Source
  to: Target
  content_type: raw_text
  
# 전체 대화 기록 (person_job용)
- from: Agent 1
  to: Agent 2
  content_type: conversation_state
  
# 코드 실행의 구조화된 데이터
- from: Code Job
  to: Person Job
  content_type: object
```

### 변수 범위와 전파

1. **Start 노드 변수**: `custom_data`를 통해 전역적으로 사용 가능
2. **연결 변수**: 대상 노드로 범위 지정
3. **코드 변수**: `result` 또는 반환 값이 전파됨
4. **템플릿 변수**: 모든 업스트림 변수에 접근 가능

## 고급 패턴

### 1. 조건을 사용한 반복 처리

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

### 2. 다중 에이전트 토론 패턴

```yaml
persons:
  Proposer:
    service: openai
    model: gpt-4.1-nano
    system_prompt: 혁신적인 솔루션을 제안합니다
    
  Critic:
    service: openai
    model: gpt-4.1-nano
    system_prompt: 제안을 비판적으로 평가합니다
    
  Synthesizer:
    service: openai
    model: gpt-4.1-nano
    system_prompt: 서로 다른 관점을 종합합니다

nodes:
  - label: Initial Proposal
    type: person_job
    props:
      person: Proposer
      first_only_prompt: '다음에 대한 솔루션 제안: {{problem}}'
      default_prompt: '비판을 바탕으로 제안을 개선하세요'
      max_iteration: 3
      memory_profile: FOCUSED
      
  - label: Critical Review
    type: person_job
    props:
      person: Critic
      default_prompt: |
        이 제안을 평가하세요:
        {{proposal}}
        
        강점과 약점을 식별하세요.
      max_iteration: 3
      memory_profile: GOLDFISH  # 매번 새로운 관점
      
  - label: Synthesize
    type: person_job
    props:
      person: Synthesizer
      default_prompt: |
        제안과 비판을 고려하여:
        제안: {{proposal}}
        비판: {{criticism}}
        
        균형 잡힌 종합을 만드세요.
      max_iteration: 1
      memory_profile: FULL
```

### 3. 오류 처리와 재시도 로직

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
        # sub_diagram을 위한 배치 구조 생성
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
      batch_parallel: true  # 모든 항목을 동시에 처리
      
  - label: Aggregate Results
    type: code_job
    props:
      code: |
        # batch_results는 각 실행의 출력 배열
        successful = [r for r in batch_results if r.get("status") == "success"]
        failed = [r for r in batch_results if r.get("status") != "success"]
        
        result = {
            "total": len(batch_results),
            "successful": len(successful),
            "failed": len(failed),
            "results": successful
        }
```

## 서브 다이어그램과 모듈식 구성

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
      passInputData: true  # 모든 변수를 서브 다이어그램에 전달
```

### 서브 다이어그램을 사용한 배치 처리

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

## 오류 처리와 복원력

### 1. 우아한 성능 저하

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
            errors.append("required_field 누락")
            
        if len(data.get("items", [])) > 1000:
            warnings.append("대용량 데이터셋은 시간이 걸릴 수 있습니다")
            
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
            
        # 서킷이 열려 있는지 확인
        now = time.time()
        if state["failures"] >= 3:
            if now - state["last_failure"] < 300:  # 5분 쿨다운
                result = {"circuit_open": True}
            else:
                # 서킷 리셋
                state["failures"] = 0
                result = {"circuit_open": False, "state": state}
        else:
            result = {"circuit_open": False, "state": state}
```

## 성능 최적화

### 1. 병렬 실행 전략

```yaml
# 병렬 데이터 가져오기
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
            # 캐시 나이 확인
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
# 데이터 크기에 따라 전략 선택
nodes:
  - label: Analyze Workload
    type: code_job
    props:
      code: |
        item_count = len(items)
        avg_size = sum(len(str(item)) for item in items) / item_count
        
        # 대용량 데이터셋에는 배치, 소량에는 순차 처리 사용
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

- **관련 노드를 시각적으로 그룹화**: x 좌표를 사용하여 흐름 진행 표시
- **설명적인 레이블 사용**: `Step 3`가 아닌 `Validate User Input`
- **일관된 위치 지정**: 가독성을 위해 x를 200-400씩 증가
- **핸들 위치**: 더 깔끔한 레이아웃을 위해 `flipped` 속성 사용

### 2. 변수 명명

```yaml
connections:
  # 좋음: 설명적이고 내용을 나타냄
  - from: Load User Data
    to: Process Users
    label: user_records
    
  # 나쁨: 일반적이고 불명확함
  - from: Node1
    to: Node2
    label: data
```

### 3. 외부 코드 구성

**외부 코드 파일을 사용해야 할 때:**
- 10-15줄보다 긴 코드
- 여러 다이어그램에서 재사용 가능한 함수
- 가져오기와 도우미 함수가 필요한 복잡한 로직
- 독립적으로 테스트가 필요한 코드
- DiPeO의 코드 생성 패턴 따르기 (모든 코드가 외부 파일에)

**디렉토리 구조:**
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

**예시: 인라인 vs 외부 코드**

```yaml
# 인라인 - 간단한 작업에 좋음
- label: Simple Transform
  type: code_job
  props:
    code: |
      result = input_data.upper()

# 외부 - 복잡한 로직에 더 나음
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
          log.info(f"{len(items)}개 항목 처리 중")
          processed = process_items(items)
          log.info(f"{len(processed)}개 항목 성공적으로 처리됨")
          result = {"success": True, "data": processed}
      except Exception as e:
          log.error(f"처리 실패: {str(e)}")
          result = {"success": False, "error": str(e)}
```

### 5. 다이어그램 테스트

```yaml
# 테스트 하네스 다이어그램
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
            raise AssertionError(f"{len(failures)}개 테스트 실패")
```

## 프로덕션 패턴

### 1. 구성 관리

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
        
        # 모니터링 시스템에 전송
        send_metrics(metrics)
        result = metrics
```

### 3. 우아한 종료

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
# 블루-그린 배포 체커
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
            result = {"deploy": False, "reason": "이미 대상 버전입니다"}
        else:
            result = {"deploy": True, "current": current, "target": target}
```

## 디버깅과 문제 해결

### 1. 디버그 모드 실행

```bash
# 디버그 출력으로 실행
dipeo run my_diagram --light --debug

# 장시간 실행 다이어그램에 타임아웃 사용
dipeo run my_diagram --light --debug --timeout=300

# 초기 데이터와 함께
dipeo run my_diagram --light --debug --input-data '{"user_id": 123}'
```

### 2. 노드 디버깅

```yaml
- label: Debug State
  type: code_job
  props:
    code: |
      # 사용 가능한 모든 변수 출력
      print("=== 디버그 상태 ===")
      for key, value in locals().items():
          if not key.startswith("_"):
              print(f"{key}: {type(value)} = {repr(value)[:100]}")
      
      # 데이터를 변경 없이 전달
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
          f.write(f"{datetime.now()}: 노드 {node_label} 실행됨\n")
          f.write(f"  입력: {json.dumps(input_data)[:200]}\n")
      result = input_data
```

### 4. 일반적인 문제와 해결책

**문제: 템플릿에서 변수를 찾을 수 없음**
```yaml
# 문제
default_prompt: "Process {{data}}"  # 'data'가 정의되지 않음

# 해결책: 연결에 레이블이 있는지 확인
connections:
  - from: Source
    to: Target
    label: data  # 이것이 'data' 변수를 생성
```

**문제: 서브 다이어그램이 입력을 받지 못함**
```yaml
# 문제
props:
  diagram_name: sub_workflow
  passInputData: false  # 입력이 전달되지 않음

# 해결책
props:
  diagram_name: sub_workflow
  passInputData: true  # 모든 변수 전달
```

**문제: 조건이 항상 거짓**
```yaml
# 문제
condition_type: custom
expression: score > 80  # 'score'가 문자열일 수 있음

# 해결책
expression: float(score) > 80  # 명시적 변환
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
        
        # 비싼 작업
        result = expensive_function(input_data)
        
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(10)  # 상위 10개 함수
        
        with open("files/logs/profile.txt", "w") as f:
            f.write(s.getvalue())
```

## 결론

DiPeO Light 포맷은 복잡한 워크플로우를 만들기 위한 강력하고 읽기 쉬운 방법을 제공합니다. 이 가이드에서 설명한 노드 타입, 데이터 흐름 패턴, 모범 사례를 이해함으로써 효율적이고 유지 관리 가능하며 프로덕션 준비가 된 다이어그램을 만들 수 있습니다.

주요 요점:
1. 변수 접근을 위해 **항상 연결에 레이블을 지정**
2. 복잡한 로직에는 **외부 코드 파일 사용**
3. 모듈성을 위해 **서브 다이어그램 활용**
4. 조건과 검증으로 **오류 계획**
5. 디버그 노드와 로깅으로 **실행 모니터링**
6. 다양한 입력 시나리오로 **철저히 테스트**

여기에 표시된 예제와 패턴은 DiPeO의 자체 코드 생성 시스템에서 파생되었으며, Light 포맷이 읽기 쉽고 유지 관리 가능한 상태를 유지하면서 정교한 실제 워크플로우를 처리할 수 있음을 보여줍니다.