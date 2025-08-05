# DiPeO 사용자 가이드: 시각적 다이어그램으로 AI 워크플로우 구축하기

DiPeO에 오신 것을 환영합니다! 이 가이드는 브라우저의 시각적 다이어그램 편집기를 사용하여 AI 기반 워크플로우를 만드는 방법을 안내합니다. 이미 DiPeO를 설치하셨다면, 바로 첫 번째 다이어그램 구축을 시작해보겠습니다.


> ### 기타 문서 목록
> - [유저 가이드](korean_guide.md)
>   - DiPeO 프로젝트 시작용 가이드
> - [프로젝트 전반 구조]()
>   - DiPeO의 전반적인 구조에 대해 다룹니다.
> - [Dog-fooding 코드 생성 사례](codegen_dog_fooding.md)
>   - DiPeO 프로젝트 다이어그램으로 코드 생성하는 사례 및 실제 적용된 내용에 대해 다룹니다.
> - [메모리 시스템 디자인](memory_system_design.md)
>   - DiPeO를 시작한 계기이기도 하면서, person과 person job을 분리한 이유, 또한 LLM 컨텍스트를 관리하는 체계에 대해 다룹니다.
> - [다이어그램 포맷](comprehensive_light_diagram_guide.md)
>   - DiPeO에서 사용하는 다이어그램을 텍스트 파일로 export하거나 import하기 위한 양식 및 작성법에 대해 다룹니다.
> - [코드 생성 가이드](code-generation-guide.md)
>   - DiPeO에서 신규 기능 개발 시 필요한 코드 생성 절차에 대해 다룹니다.


## 목차
1. [시작하기](#시작하기)
2. [핵심 개념](#핵심-개념)
3. [첫 번째 다이어그램](#첫-번째-다이어그램)
4. [노드 작업하기](#노드-작업하기)
5. [AI 에이전트(Persons) 관리하기](#ai-에이전트persons-관리하기)
6. [노드 연결하기](#노드-연결하기)
7. [다이어그램 실행하기](#다이어그램-실행하기)
8. [일반적인 패턴](#일반적인-패턴)
9. [팁과 모범 사례](#팁과-모범-사례)

## 시작하기

### DiPeO 열기

1. 서버가 실행 중인지 확인하세요:
   ```bash
   make dev-all
   ```

2. 브라우저를 열고 다음 주소로 이동하세요: `http://localhost:3000`

3. DiPeO 다이어그램 편집기 인터페이스가 표시됩니다:
   - **왼쪽 사이드바**: 노드 팔레트와 컨트롤
   - **중앙 캔버스**: 다이어그램을 구축하는 공간
   - **오른쪽 사이드바**: 선택된 요소의 속성 패널

## 핵심 개념

다이어그램을 구축하기 전에 주요 개념을 이해해봅시다:

### 1. **Persons** (AI 에이전트)
- "Person"은 LLM 인스턴스입니다 (예: GPT-4)
- 각 Person은 자체 메모리와 컨텍스트를 가집니다
- 여러 노드가 동일한 Person을 사용할 수 있습니다
- 서로 다른 역할을 가진 팀 멤버로 생각하세요

### 2. **노드** (작업)
- 노드는 워크플로우의 구성 요소입니다
- 각 노드는 특정 작업을 수행합니다
- 일반적인 유형: `person_job` (AI 작업), `code_job` (코드 실행), `condition` (분기)

### 3. **연결** (데이터 흐름)
- 노드를 연결하는 화살표
- 다이어그램을 통한 데이터 흐름을 정의합니다
- 다양한 유형의 콘텐츠를 전달할 수 있습니다 (텍스트, 변수, 대화 상태)

### 4. **핸들**
- 노드의 연결 지점
- **왼쪽**: 입력 핸들 (데이터 수신)
- **오른쪽**: 출력 핸들 (데이터 전송)
- `first`와 같은 특수 핸들 (초기 전용 입력)

## 첫 번째 다이어그램

간단한 Q&A 어시스턴트를 만들어봅시다:

### 1단계: API 키 설정

1. 왼쪽 사이드바에서 **"API Keys"** 버튼을 클릭하세요
2. OpenAI API 키를 추가하세요
3. 기억하기 쉬운 ID를 지정하세요 (예: "APIKEY_MAIN")

### 2단계: Person 생성

1. 왼쪽 사이드바에서 **"Add Person"**을 클릭하세요
2. 설정:
   - **Name**: "Assistant"
   - **Service**: OpenAI
   - **Model**: gpt-4o-mini (또는 선호하는 모델)
   - **API Key**: 키 선택
   - **System Prompt**: "You are a helpful assistant"
3. **Save** 클릭

### 3단계: 다이어그램 구축

1. **Start 노드 추가**:
   - 왼쪽 팔레트에서 "Start"를 캔버스로 드래그
   - 다이어그램의 진입점입니다

2. **사용자 입력 노드 추가**:
   - "User Response"를 캔버스로 드래그
   - 클릭하여 설정:
     - **Prompt**: "What would you like to know?"
     - **Timeout**: 120초

3. **AI 응답 노드 추가**:
   - "Person Job"을 캔버스로 드래그
   - 설정:
     - **Person**: "Assistant" 선택
     - **Default Prompt**: "Answer this question: {{question}}"
     - **Max Iteration**: 1

4. **엔드포인트 추가**:
   - "Endpoint"를 캔버스로 드래그
   - 설정:
     - **Save to File**: Yes
     - **File Format**: txt
     - **File Path**: `files/results/answer.txt`

### 4단계: 노드 연결

1. **Start를 User Response에 연결**:
   - Start의 출력 핸들에서 User Response의 입력 핸들로 클릭하여 드래그

2. **User Response를 Person Job에 연결**:
   - User Response 출력에서 Person Job 입력으로 드래그
   - 연결선 클릭
   - **Label** 설정: "question" (이것이 `{{question}}` 변수를 생성합니다)

3. **Person Job을 Endpoint에 연결**:
   - Endpoint에 연결하여 흐름 완성

### 5단계: 다이어그램 저장

상단 툴바에서 **"Quicksave"**를 클릭하여 작업을 저장하세요.

## 노드 작업하기

### Person Job (AI 작업)
AI 워크플로우에서 가장 중요한 노드:

```yaml
persons:
    Person: 사용할 AI 에이전트 label
    - Default Prompt: 메인 지시 템플릿
    - First Only Prompt: 첫 번째 반복에만 사용되는 특별한 프롬프트
    - Max Iteration: 실행 가능한 최대 횟수
    - Memory Profile: 기억할 컨텍스트 양
      - FULL: 모든 것을 기억
      - FOCUSED: 최근 20개 교환
      - MINIMAL: 최근 5개 메시지
      - GOLDFISH: 마지막 2개 메시지만
```

### Code Job (코드 실행)
Python, JavaScript, 또는 Bash 코드 실행:

```python
# 입력 변수 접근
user_input = inputs.get('user_data', '')

# 데이터 처리
result = user_input.upper()

# 중요: 데이터를 전달하려면 'result' 변수 또는 'return' 사용
result = f"Processed: {result}"
```

### Condition (분기)
결정 지점 생성:
- **Detect Max Iterations**: 루프 종료 확인
- **Custom Expression**: `score > 80`과 같은 Python 표현식 사용

### DB (파일 작업)
파일에서 데이터 읽기:
```yaml
Operation: read
Sub Type: file
Source: files/data/input.csv
```

## AI 에이전트(Persons) 관리하기

### 특화된 에이전트 생성

다양한 역할을 위해 서로 다른 Persons 생성:

1. **분석가**:
   ```yaml
   System Prompt: "You analyze data and identify patterns. Be objective and thorough."
   ```

2. **작가**:
   ```yaml
   System Prompt: "You write clear, engaging content. Focus on readability."
   ```

3. **비평가**:
   ```yaml
   System Prompt: "You provide constructive criticism. Be specific about improvements."
   ```

### 메모리 관리

에이전트가 대화를 기억하는 방식 제어:

- **토론**: GOLDFISH 사용 (에이전트가 이전 포인트에 갇히지 않고 논쟁)
- **분석**: FULL 사용 (완전한 컨텍스트 유지)
- **빠른 작업**: MINIMAL 사용 (충분한 컨텍스트만)

## 노드 연결하기

### 연결 유형

1. **raw_text**: 일반 텍스트 출력
2. **conversation_state**: 전체 대화 기록
3. **object**: 복잡한 데이터 구조

### 레이블 사용

레이블은 참조할 수 있는 변수를 생성합니다:

```yaml
연결: User Input → AI Task
레이블: user_question
사용: 프롬프트에서 {{user_question}}
```

### 특수 핸들

- **_first**: 첫 번째 실행에만 데이터 수용
- **_condtrue/_condfalse**: 조건 노드 출력

## 다이어그램 실행하기

### 실행 모드

1. **"Execution Mode"**로 전환 (상단 툴바)
2. **"Run Diagram"** 클릭
3. 프롬프트를 따라가며 실시간으로 실행 관찰

### 모니터링

- 녹색 하이라이트는 활성 노드를 표시
- 노드를 클릭하여 출력 확인
- 자세한 로그는 콘솔 확인

### 디버깅

- 자세한 출력을 위해 **Debug Mode** 사용
- 데이터 검사를 위해 Code Job 노드 추가:
  ```python
  print(f"Current data: {inputs}")
  result = inputs  # 검사를 위해 통과
  ```

## 일반적인 패턴

### 1. 간단한 Q&A
```
Start → User Input → AI Response → Save Result
```

### 2. 반복적 개선
```
Start → Initial Draft → [Loop: Critique → Revise] → Final Output
```

### 3. 다중 에이전트 토론
```
Topic → Agent A (argument) → Agent B (counter) → Judge → Result
```

### 4. 데이터 처리 파이프라인
```
Load Data → Validate → Transform → AI Analysis → Report
```

### 5. 연구 어시스턴트
```
Query → Web Search → Fact Check → Synthesize → Output
```

## 팁과 모범 사례

### 1. 단순하게 시작
- 먼저 기본 흐름 구축
- 복잡성을 추가하기 전에 각 섹션 테스트
- 자주 저장/로드 사용

### 2. 변수 이름 지정
- 명확하고 설명적인 레이블 사용
- 일관된 이름 유지: `user_input`, `processed_data`
- 복잡한 변수는 노드 설명에 문서화

### 3. 오류 처리
- 오류 확인을 위한 조건 노드 추가
- 처리 전 검증 사용
- 폴백 경로 포함

### 4. 성능
- 무한 루프 방지를 위해 반복 제한
- 적절한 메모리 프로필 사용
- 타임아웃 설정 고려

### 5. 정리
- 관련 노드를 시각적으로 그룹화
- 일관된 왼쪽에서 오른쪽 흐름 사용
- 복잡한 노드에 설명 추가

### 6. 테스트
- 먼저 작은 테스트 데이터 사용
- 실행 로그 모니터링
- 성공적인 패턴을 템플릿으로 저장

## 고급 기능

### 도구 사용
Person Job 노드에 도구 활성화:
- **Web Search**: 실시간 정보
- **Image Generation**: 시각 자료 생성

### 템플릿
재사용 가능한 패턴 생성:
1. 다이어그램 구축
2. 설명적인 이름으로 저장
3. 새로운 사용 사례를 위해 로드 및 수정

### 다중 출력
조건 노드를 사용하여 여러 경로 생성:
```
Analysis → Condition (quality > 80) 
         ├─→ (true) → Publish
         └─→ (false) → Revise
```

## 문제 해결

### 일반적인 문제

1. **"No Person selected"**: 먼저 Person을 생성하고 할당
2. **"Variable not found"**: 연결 레이블 확인
3. **"Timeout reached"**: 타임아웃 증가 또는 프롬프트 단순화
4. **"Max iterations"**: max_iteration 설정 조정

### 도움 받기

- `files/diagrams/examples/`의 예제 다이어그램 확인
- 실행 모드에서 로그 검토
- 메모리 프로필 실험
- 작동하는 예제로 시작하여 수정

## 다음 단계

1. **예제 탐색**: 예제 다이어그램 로드 및 학습
2. **템플릿 구축**: 자신만의 재사용 가능한 패턴 생성
3. **실험**: 다양한 노드 조합 시도
4. **공유**: 다이어그램을 내보내어 다른 사람과 공유

기억하세요: DiPeO는 시각적 실험에 관한 것입니다. 새로운 조합을 시도하고 사용 사례에 가장 적합한 것을 찾는 것을 두려워하지 마세요!