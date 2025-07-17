# DiPeO Light 포맷 가이드

Light 포맷은 DiPeO 다이어그램을 생성하기 위한 간소화된 YAML 문법입니다. ID 대신 사람이 읽을 수 있는 레이블을 사용하여 워크플로우를 더 쉽게 작성하고 이해할 수 있습니다.

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

# 필수: nodes 정의
nodes:
  - label: Node Label
    type: node_type
    position: {x: 100, y: 200}
    props:
      # 노드별 속성

# 선택사항: connections 정의
connections:
  - from: Source Node
    to: Target Node
    content_type: raw_text  # 또는 variable, conversation_state
    label: optional_label
```

## 노드 타입

### 1. **start** - 진입점

모든 다이어그램은 정확히 하나의 start 노드를 가져야 합니다:

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
    default_prompt: '{{topic}}에 대한 이야기를 작성하세요'
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
- **GOLDFISH**: 마지막 2개 메시지만, 시스템 보존 안 함

### 3. **condition** - 분기 로직

조건에 따른 흐름 제어:

```yaml
- label: Check Iterations
  type: condition
  position: {x: 600, y: 400}
  props:
    condition_type: detect_max_iterations  # 모든 person_job 노드가 최대치에 도달했는지 확인
    flipped: true  # 선택사항: true/false 출력 반전

# 사용자 정의 표현식 조건
- label: Check Value
  type: condition
  position: {x: 600, y: 400}
  props:
    condition_type: custom
    expression: a > 10  # Python 표현식
```

### 4. **code_job** - 코드 실행

Python, JavaScript, 또는 Bash 코드 실행:

```yaml
- label: Process Data
  type: code_job
  position: {x: 400, y: 200}
  props:
    code_type: python  # 또는 javascript, bash
    code: |
      # 컨텍스트에서 변수 접근
      print(f"입력값: {input_value}")
      result = input_value * 2
      # 'result' 변수는 자동으로 다음 노드로 전달됨
```

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

API 호출하기:

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

노드 간 단순 흐름:

```yaml
connections:
  - from: Start
    to: Process Data
```

### 조건 분기

조건 노드는 두 개의 출력 핸들을 가집니다:

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
    content_type: variable        # 코드 실행에서의 변수
```

### 이름이 지정된 연결

변수 접근을 위한 연결 레이블:

```yaml
connections:
  - from: Load Data
    to: Process_first  # 첫 번째 전용 입력을 위한 특수 핸들
    label: topic       # 프롬프트에서 {{topic}}으로 접근
```

## 변수와 데이터 흐름

### 템플릿 변수

프롬프트에서 `{{variable_name}}` 문법 사용:

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
    default_prompt: '안녕하세요 {{name}}님! 오늘 어떻게 도와드릴까요?'

connections:
  - from: Get User Name
    to: Greet User
    label: name  # 출력을 {{name}}으로 사용 가능하게 함
```

### 코드 변수

코드에서 설정된 변수는 자동으로 후속 노드에서 사용 가능:

```yaml
- label: Calculate
  type: code_job
  props:
    code: |
      a = 10
      b = 20
      result = a + b  # 'result'는 다음 노드로 전달됨

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
    to: Counter  # 루프백
    
  - from: Check Complete_condtrue
    to: End  # 루프 종료
```

### 토론 패턴

여러 에이전트 상호작용:

```yaml
persons:
  Optimist:
    service: openai
    model: gpt-4.1-nano
    system_prompt: 항상 긍정적인 면을 보세요
    
  Pessimist:
    service: openai
    model: gpt-4.1-nano
    system_prompt: 잠재적인 문제점을 지적하세요

nodes:
  - label: Optimist View
    type: person_job
    props:
      person: Optimist
      first_only_prompt: '다음에 대한 해결책을 제안하세요: {{problem}}'
      default_prompt: '비판에 응답하세요'
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
    content_type: variable
```

## 완전한 예제

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
      prompt: '무엇을 알고 싶으신가요?'
      
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

### 예제 2: 반복 코드 실행

```yaml
version: light

nodes:
  - label: Start
    type: start
    position: {x: 50, y: 200}
    
  - label: Initialize
    type: code_job
    position: {x: 200, y: 200}
    props:
      code_type: python
      code: |
        counter = 0
        result = "시작..."
        
  - label: Process
    type: code_job
    position: {x: 400, y: 200}
    props:
      code_type: python
      code: |
        counter += 1
        print(f"반복 {counter}")
        result = f"{counter}번 처리됨"
        
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
    to: Process  # 루프백
  - from: Check Done_condtrue
    to: End
```

## 모범 사례

1. **설명적인 레이블 사용** - 레이블은 고유 식별자이므로 의미 있게 만드세요
2. **적절한 메모리 프로필 설정** - 토론 패턴에는 GOLDFISH, 컨텍스트 인식 대화에는 FULL 사용
3. **에러를 우아하게 처리** - 에러 확인을 위한 조건 노드 추가
4. **반복적으로 테스트** - 단순하게 시작하여 점진적으로 복잡성 추가
5. **주석 사용** - YAML은 문서화를 위한 # 주석 지원
6. **변수 이름 지정** - 템플릿에서 명확하고 일관된 변수 이름 사용
7. **노드를 논리적으로 배치** - 왼쪽에서 오른쪽 흐름이 가독성을 향상시킴

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

- 공백이 있는 레이블도 잘 작동합니다: `label: My Complex Node`
- 중복 레이블은 자동으로 번호가 매겨집니다: `Process` → `Process~1`
- 노드의 `flipped` 속성은 핸들 위치를 시각적으로 반전시킵니다
- 초기화에는 `first_only_prompt`, 반복에는 `default_prompt` 사용
- `web_search_preview` 같은 도구는 확장된 기능을 활성화합니다
- `_first` 핸들 접미사는 특별한 첫 번째 입력을 허용합니다

Light 포맷은 완전성보다 가독성과 편집의 용이성을 우선시하므로 빠른 프로토타이핑과 간단한 워크플로우에 이상적입니다.