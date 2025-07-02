# DiPeO Light 형식 가이드

Light 형식은 DiPeO 다이어그램을 작성하기 위한 간소화된 YAML 문법입니다. ID 대신 사람이 읽기 쉬운 라벨을 사용하여 작성과 이해가 더 쉽습니다.

## 기본 구조

```yaml
version: light

persons:
  Writer:
    label: Writer
    service: openai
    model: gpt-4o-mini
    system_prompt: You are a creative writer.
    api_key_id: APIKEY_3A9F1D

nodes:
  - label: Start
    type: start
    position: {x: 50, y: 200}
    
  - label: Process Data
    type: job
    position: {x: 250, y: 200}
    props:
      code_type: python
      code: |
        # Your Python code here
        result = input_data * 2
        return result

connections:
  - from: Start
    to: Process Data
  - from: Process Data
    to: End Result
```

## 노드 타입

### 1. **start** - 진입점
```yaml
- label: Start
  type: start
  position: {x: 50, y: 200}
```

### 2. **person_job** - AI 기반 작업
```yaml
- label: Story Writer
  type: person_job
  position: {x: 400, y: 200}
  props:
    person: Writer  # 위에서 정의한 person 참조
    default_prompt: 'Write a story about: {{topic}}'
    first_only_prompt: '첫 번째 반복에서만 사용할 프롬프트'
    max_iteration: 3
    forgetting_mode: on_every_turn  # 또는 no_forget, upon_request
```

### 3. **condition** - 분기 로직
```yaml
- label: Check Quality
  type: condition
  position: {x: 600, y: 200}
  props:
    personId: Reviewer
    prompt: 'Is this story good enough?'
```

### 4. **job** - 코드 실행
```yaml
- label: Transform Data
  type: job
  position: {x: 400, y: 200}
  props:
    code_type: python  # 또는 javascript, bash
    code: |
      # 입력 처리
      return {"result": input_data.upper()}
```

### 5. **endpoint** - 출력/저장
```yaml
- label: Save Result
  type: endpoint
  position: {x: 800, y: 200}
  props:
    save_to_file: true
    file_path: files/results/output.txt
```

### 6. **db** - 데이터베이스/파일 작업
```yaml
- label: Load Data
  type: db
  position: {x: 200, y: 200}
  props:
    operation: read
    sub_type: file
    source_details: files/data/input.json
```

### 7. **user_response** - 사용자 입력
```yaml
- label: Ask User
  type: user_response
  position: {x: 400, y: 300}
  props:
    prompt: 'Please enter your choice:'
    timeout: 60
```

## 연결 (Connections)

### 단순 연결
```yaml
connections:
  - from: Node A
    to: Node B
```

### 커스텀 핸들 사용
```yaml
connections:
  - from: Condition:True    # 조건의 True 분기
    to: Success Node
  - from: Condition:False   # False 분기
    to: Retry Node
```

### 콘텐츠 타입과 라벨 포함
```yaml
connections:
  - from: Source Node
    to: Target Node
    content_type: variable     # 또는 raw_text, conversation_state
    label: user_input
```

## 변수와 데이터 흐름

`{{variable_name}}` 문법을 사용하여 노드 간에 변수를 전달할 수 있습니다:

```yaml
- label: Get Name
  type: user_response
  props:
    prompt: 'What is your name?'

- label: Greet User
  type: person_job
  props:
    person: Assistant
    default_prompt: 'Say hello to {{name}}'
```

## 전체 예제

```yaml
version: light

persons:
  Assistant:
    label: Assistant
    service: openai
    model: gpt-4o-mini
    system_prompt: You are a helpful assistant.
    api_key_id: MY_API_KEY

nodes:
  - label: Start
    type: start
    position: {x: 50, y: 200}

  - label: Load Topic
    type: db
    position: {x: 200, y: 200}
    props:
      operation: read
      sub_type: file
      source_details: files/prompts/topic.txt

  - label: Generate Content
    type: person_job
    position: {x: 400, y: 200}
    props:
      person: Assistant
      default_prompt: 'Write an article about: {{topic}}'
      max_iteration: 1

  - label: Save Article
    type: endpoint
    position: {x: 600, y: 200}
    props:
      save_to_file: true
      file_path: files/results/article.txt

connections:
  - from: Start
    to: Load Topic
    
  - from: Load Topic
    to: Generate Content
    label: topic
    
  - from: Generate Content
    to: Save Article
```

## 팁

1. **라벨은 고유 식별자입니다** - 각 노드는 고유한 라벨을 가져야 합니다
2. **위치는 선택사항입니다** - 생략하면 노드가 자동으로 배치됩니다
3. **Props는 노드별 데이터를 포함합니다** - 노드 타입마다 필요한 props가 다릅니다
4. **Forgetting mode는 person_job 노드의 대화 메모리를 제어합니다**
5. **의미 있는 라벨을 사용하세요** - 다이어그램을 자체 문서화합니다

Light 형식은 완전성보다 가독성과 편집 용이성을 우선시하므로, 빠른 프로토타이핑과 간단한 워크플로우에 이상적입니다.