# DiPeO Light 형식 가이드

Light 형식은 DiPeO 다이어그램을 생성하기 위한 간소화된 YAML 구문입니다. ID 대신 사람이 읽을 수 있는 레이블을 사용하여 워크플로우를 더 쉽게 작성하고 이해할 수 있게 해줍니다.

## 기본 구조

모든 Light 다이어그램은 다음 구조를 따릅니다:

```yaml
version: light

# 선택사항: persons(AI 에이전트) 정의
persons:
  Person 1:
    service: openai
    model: gpt-4.1-nano
    api_key_id: APIKEY_123456
    system_prompt: 선택적 시스템 프롬프트

# 필수: 노드 정의
nodes:
  - label: 노드 레이블
    type: node_type
    position: {x: 100, y: 200}
    props:
      # 노드별 속성

# 선택사항: 연결 정의
connections:
  - from: 소스 노드
    to: 대상 노드
    content_type: raw_text  # 또는 conversation_state, object
    label: optional_label
```

## 노드 타입

### 1. **start** - 진입점

모든 다이어그램은 정확히 하나의 시작 노드를 가져야 합니다:

```yaml
- label: Start
  type: start
  position: {x: 50, y: 200}
  props:
    trigger_mode: manual  # 또는 automatic
```

### 2. **person_job** - AI 기반 작업

LLM 에이전트로 프롬프트 실행:

```yaml
- label: Writer
  type: person_job
  position: {x: 400, y: 200}
  props:
    person: Person 1  # persons 섹션 참조
    default_prompt: '{{topic}}에 대한 이야기를 써주세요'
    first_only_prompt: '{{topic}}에 대한 이야기를 시작하세요'  # 첫 번째 반복에서만 사용
    max_iteration: 3
    memory_profile: FULL  # 또는 FOCUSED, MINIMAL, GOLDFISH
    tools:  # 선택적 도구
    - type: web_search_preview
      enabled: true
```

메모리 프로필은 대화 기록을 제어합니다:
- **FULL**: 모든 메시지 보존
- **FOCUSED**: 최근 20개 대화 쌍
- **MINIMAL**: 시스템 메시지 + 최근 5개 메시지
- **GOLDFISH**: 마지막 2개 메시지만, 시스템 보존 없음

### 3. **condition** - 분기 로직

조건에 따른 흐름 제어:

```yaml
- label: Check Iterations
  type: condition
  position: {x: 600, y: 400}
  props:
    condition_type: detect_max_iterations  # 모든 person_job 노드가 최대치에 도달했는지 확인
    flipped: true  # 선택사항: true/false 출력 뒤집기

# 사용자 정의 표현식 조건
- label: Check Value
  type: condition
  position: {x: 600, y: 400}
  props:
    condition_type: custom
    expression: a > 10  # Python 표현식
```

### 4. **code_job** - 코드 실행

Python, TypeScript, Bash 또는 Shell 코드를 인라인이나 외부 파일에서 실행:

#### 옵션 1: 인라인 코드

```yaml
- label: Process Data
  type: code_job
  position: {x: 400, y: 200}
  props:
    code_type: python  # 또는 typescript, bash, shell
    code: |
      # 연결에서 입력 변수 접근
      data = raw_data  # 'raw_data' 레이블이 붙은 연결의 변수
      
      # 데이터 처리
      processed = data.upper()
      
      # 중요: 다음 노드에 데이터를 전달하려면 다음 중 하나를 사용:
      # 1. 'result' 변수에 할당
      result = processed
      
      # 2. 또는 return 문 사용
      # return processed
      
      # 주의: print()는 code_job 노드에서 지원되지 않음
      # 'result'에 할당되지 않은 변수는 전달되지 않음
```

#### 옵션 2: 외부 코드 파일 (복잡한 로직에 권장)

```yaml
- label: Process Data
  type: code_job
  position: {x: 400, y: 200}
  props:
    code_type: python  # 또는 typescript, bash, shell
    code: files/code/my_functions.py  # 코드 파일 경로
    functionName: process_data  # 호출할 특정 함수

# 외부 파일에는 다음이 포함되어야 함:
# def process_data(raw_data, other_input):
#     processed = raw_data.upper()
#     return processed
```

**code_job 중요 사항:**
- 들어오는 연결의 변수는 레이블 이름으로 사용 가능
- 인라인 코드의 경우, 반드시 다음 중 하나를 수행해야 함:
  - 출력을 `result`라는 변수에 할당
  - `return` 문 사용 (코드가 함수로 래핑됨)
- 외부 파일의 경우:
  - `code` 필드에 파일 경로 지정
  - `functionName`으로 호출할 함수 지정
  - 함수는 입력 변수를 인수로 받음
  - 함수의 반환값이 후속 노드로 전달됨
- (인라인에서) `result`나 `return`을 사용하지 않으면, 노드는 "Code executed successfully"를 출력
- `print()` 함수는 지원되지 않으며 출력을 생성하지 않음

### 5. **endpoint** - 출력/저장

결과를 파일로 저장:

```yaml
- label: Save Result
  type: endpoint
  position: {x: 800, y: 200}
  props:
    file_format: txt  # 또는 json, yaml, md
    save_to_file: true
    file_path: files/results/output.txt
```

### 6. **db** - 데이터베이스/파일 작업

파일에서 데이터 읽기:

```yaml
- label: Load Data
  type: db
  position: {x: 200, y: 200}
  props:
    operation: read
    sub_type: file
    source_details: files/data/input.txt
```

### 7. **api_job** - HTTP 요청

API 호출:

```yaml
- label: Call API
  type: api_job
  position: {x: 400, y: 200}
  props:
    url: https://api.example.com/data
    method: GET
    headers:
      Authorization: Bearer {{api_token}}
```

### 8. **user_response** - 사용자 입력

사용자로부터 입력 받기:

```yaml
- label: Ask Question
  type: user_response
  position: {x: 400, y: 200}
  props:
    prompt: '이름을 입력해주세요:'
    timeout: 60
```

## 연결

### 기본 연결

노드 간 단순한 흐름:

```yaml
connections:
  - from: Start
    to: Process Data
```

### 조건 분기

조건은 두 개의 출력 핸들을 가집니다:

```yaml
connections:
  - from: Check Value_condtrue   # 조건이 참일 때
    to: Success Node
  - from: Check Value_condfalse  # 조건이 거짓일 때
    to: Retry Node
```

### 콘텐츠 타입

노드 간 데이터 흐름 방식 지정:

```yaml
connections:
  - from: Source
    to: Target
    content_type: raw_text         # 일반 텍스트 출력
    
  - from: Person Job
    to: Another Person
    content_type: conversation_state  # 전체 대화 기록
    
  - from: Code Job
    to: Person Job
    content_type: object          # 코드 실행의 구조화된 데이터
```

### 이름이 지정된 연결 (중요!)

**노드 간 데이터 전달을 위해서는 레이블이 필수입니다.** 레이블이 없으면 수신 노드가 데이터에 접근할 수 없습니다:

```yaml
connections:
  # 레이블 없음 - 데이터에 접근 불가
  - from: Load Data
    to: Process Data
    
  # 레이블 있음 - 'raw_data' 변수로 데이터 접근 가능
  - from: Load Data
    to: Process Data
    label: raw_data    # code_job에서: raw_data로 접근
                      # 템플릿에서: {{raw_data}}로 접근
    
  # 서로 다른 레이블로 여러 입력
  - from: Load Config
    to: Process Data
    label: config     # 별도의 'config' 변수로 접근 가능
```

**핵심 사항:**
- DB 노드(파일 작업)는 파일 내용을 반환
- 레이블은 수신 노드에서 변수 이름이 됨
- 레이블이 없으면 데이터는 전달되지만 이름으로 접근할 수 없음

## 변수와 데이터 흐름

### 템플릿 변수

프롬프트에서 `{{variable_name}}` 구문 사용:

```yaml
# 데이터를 제공하는 노드
- label: Get User Name
  type: user_response
  props:
    prompt: '이름이 무엇인가요?'

# 데이터를 사용하는 노드
- label: Greet User
  type: person_job
  props:
    person: Assistant
    default_prompt: '안녕하세요 {{name}}님! 무엇을 도와드릴까요?'

connections:
  - from: Get User Name
    to: Greet User
    label: name  # 출력을 {{name}}으로 사용 가능하게 함
```

### 코드 변수

코드에서 설정된 변수는 후속 노드에서 자동으로 사용 가능:

```yaml
- label: Calculate
  type: code_job
  props:
    code: |
      a = 10
      b = 20
      result = a + b  # 'result'가 다음 노드로 전달됨

- label: Check Result
  type: condition
  props:
    condition_type: custom
    expression: result > 25  # 이전 코드의 'result' 사용
```

## 반복 패턴

### 단순 루프

```yaml
nodes:
  - label: Counter
    type: person_job
    props:
      person: Assistant
      default_prompt: '반복 횟수 세기'
      max_iteration: 5
      
  - label: Check Complete
    type: condition
    props:
      condition_type: detect_max_iterations
      
connections:
  - from: Counter
    to: Check Complete
    content_type: conversation_state
    
  - from: Check Complete_condfalse
    to: Counter  # 다시 돌아가기
    
  - from: Check Complete_condtrue
    to: End  # 루프 종료
```

### 토론 패턴

여러 에이전트의 상호작용:

```yaml
persons:
  Optimist:
    service: openai
    model: gpt-4.1-nano
    system_prompt: 항상 긍정적인 면을 보세요
    
  Pessimist:
    service: openai
    model: gpt-4.1-nano
    system_prompt: 잠재적인 문제를 지적하세요

nodes:
  - label: Optimist View
    type: person_job
    props:
      person: Optimist
      first_only_prompt: '다음 문제에 대한 해결책 제안: {{problem}}'
      default_prompt: '비판에 대해 응답하세요'
      max_iteration: 3
      memory_profile: GOLDFISH  # 이전 라운드 잊기
      
  - label: Pessimist View
    type: person_job
    props:
      person: Pessimist
      default_prompt: '이 해결책을 비판하세요'
      max_iteration: 3
      memory_profile: GOLDFISH
      
connections:
  - from: Optimist View
    to: Pessimist View
    content_type: conversation_state
    
  - from: Pessimist View
    to: Optimist View
    content_type: raw_text
```

## 전체 예제

### 예제 1: 간단한 Q&A 봇

```yaml
version: light

persons:
  Assistant:
    service: openai
    model: gpt-4.1-nano
    api_key_id: APIKEY_123456

nodes:
  - label: Start
    type: start
    position: {x: 50, y: 200}
    
  - label: Ask Question
    type: user_response
    position: {x: 200, y: 200}
    props:
      prompt: '무엇이 궁금하신가요?'
      
  - label: Answer
    type: person_job
    position: {x: 400, y: 200}
    props:
      person: Assistant
      default_prompt: '이 질문에 답하세요: {{question}}'
      max_iteration: 1
      
  - label: Save Answer
    type: endpoint
    position: {x: 600, y: 200}
    props:
      file_format: txt
      save_to_file: true
      file_path: files/results/answer.txt

connections:
  - from: Start
    to: Ask Question
  - from: Ask Question
    to: Answer
    label: question
  - from: Answer
    to: Save Answer
```

### 예제 2: 외부 파일을 사용한 반복적 코드 실행

```yaml
version: light

# 외부 파일 (files/code/iteration_functions.py)에는 다음이 포함:
# def initialize_counter():
#     return {"counter": 0, "status": "시작하는 중..."}
#
# def increment_counter(counter, status):
#     new_counter = counter + 1
#     return {"counter": new_counter, "status": f"{new_counter}번 처리됨"}

nodes:
  - label: Start
    type: start
    position: {x: 50, y: 200}
    
  - label: Initialize
    type: code_job
    position: {x: 200, y: 200}
    props:
      code_type: python
      code: files/code/iteration_functions.py
      functionName: initialize_counter
        
  - label: Process
    type: code_job
    position: {x: 400, y: 200}
    props:
      code_type: python
      code: files/code/iteration_functions.py
      functionName: increment_counter
        
  - label: Check Done
    type: condition
    position: {x: 400, y: 400}
    props:
      condition_type: custom
      expression: counter >= 5
      
  - label: End
    type: endpoint
    position: {x: 600, y: 400}
    props:
      file_format: txt
      save_to_file: true
      file_path: files/results/iterations.txt

connections:
  - from: Start
    to: Initialize
  - from: Initialize
    to: Process
  - from: Process
    to: Check Done
  - from: Check Done_condfalse
    to: Process  # 다시 돌아가기
  - from: Check Done_condtrue
    to: End
```

## 모범 사례

1. **설명적인 레이블 사용** - 레이블은 고유 식별자이므로 의미 있게 만드세요
2. **적절한 메모리 프로필 설정** - 토론 패턴에는 GOLDFISH, 문맥 인식 대화에는 FULL 사용
3. **오류를 우아하게 처리** - 오류 확인을 위한 조건 노드 추가
4. **반복적으로 테스트** - 단순하게 시작하여 점진적으로 복잡도 추가
5. **주석 사용** - YAML은 문서화를 위한 # 주석 지원
6. **변수 명명** - 명확하고 일관된 변수 이름을 템플릿에서 사용
7. **노드를 논리적으로 배치** - 왼쪽에서 오른쪽 흐름이 가독성 향상
8. **코드 구성** - 복잡한 로직(10줄 이상)이나 재사용 가능한 함수에는 외부 파일 사용

## Light 다이어그램 실행

다이어그램 실행:

```bash
dipeo run your_diagram --light --debug
```

또는 웹 인터페이스에서 보기:
```
http://localhost:3000/?diagram=light/your_diagram.yaml
```

## 팁

- 공백이 있는 레이블도 문제없음: `label: My Complex Node`
- 중복 레이블은 자동으로 번호가 매겨짐: `Process` → `Process~1`
- 노드의 `flipped` 속성은 핸들 위치를 시각적으로 반전
- 초기화에는 `first_only_prompt`, 반복에는 `default_prompt` 사용
- `web_search_preview` 같은 도구로 확장 기능 활성화
- `_first` 핸들 접미사는 특별한 첫 번째 입력 허용

Light 형식은 완전성보다 가독성과 편집 용이성을 우선시하여 빠른 프로토타이핑과 간단한 워크플로우에 이상적입니다.