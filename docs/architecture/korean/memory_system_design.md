# DiPeO의 메모리 시스템 설계

## 개요

DiPeO는 LLM 에이전트(Person)가 공유되는 전역 대화를 서로 다르게 바라볼 수 있도록 하는 지능형 메모리 관리 시스템을 구현합니다. 이 시스템은 사용자에게는 단순하지만, LLM 기반 선택을 통해 강력하게 동작하도록 설계되었습니다.

## 듀얼 퍼소나(Dual-Persona) 메모리 셀렉터

지능형 선택이 필요할 때 메모리 시스템은 “듀얼 퍼소나” 방식을 사용합니다:

```

┌─────────────────────────────────────────────────────────────────────┐
│                     메모리 선택 프로세스                             │
│                                                                      │
│  전역 대화(Global Conversation)                                      │
│  ┌─────────────┐                                                    │
│  │ Message 1   │     ┌──────────────────────┐                      │
│  │ Message 2   │────▶│  셀렉터 파셋 🧠       │                      │
│  │ Message 3   │     │  (Alice.\_\_selector)  │                      │
│  │ Message 4   │     │                      │                      │
│  │ Message 5   │     │ "요구사항과 API       │                      │
│  │ ...         │     │  설계 관련 메시지를   │                      │
│  │ Message N   │     │  찾아라"             │                      │
│  └─────────────┘     └──────────┬───────────┘                      │
│                                  │                                  │
│                                  ▼                                  │
│                          분석 & 선택                                │
│                                  │                                  │
│                                  ▼                                  │
│                      선택된 메시지 \[2,5,7]                           │
│                                  │                                  │
│                                  ▼                                  │
│                      ┌──────────────────────┐                      │
│                      │   기본 퍼슨 👤        │                      │
│                      │      (Alice)         │                      │
│                      │                      │                      │
│                      │  다음만 봄:          │                      │
│                      │  - Message 2         │                      │
│                      │  - Message 5         │                      │
│                      │  - Message 7         │                      │
│                      └──────────────────────┘                      │
│                                  │                                  │
│                                  ▼                                  │
│                          작업 실행                                  │
└─────────────────────────────────────────────────────────────────────┘

````

**핵심 인사이트**: 동일한 퍼슨이 두 개의 존재로 분리됩니다:
- **셀렉터 파셋**(`{person_id}.__selector`): 모든 메시지를 검토하는 지능형 분석가
- **기본 퍼슨**(`{person_id}`): 선택된 메시지만 보고 작업을 수행하는 실행자

## 간단한 메모리 구성

### 사용자 옵션은 단 두 가지

1. **자연어 선택**(키워드가 아닌 문자열에 대한 기본값)
   ```yaml
   memorize_to: "requirements, API design, authentication"
````

LLM이 지정한 기준을 바탕으로 관련 메시지를 지능적으로 선택합니다.

2. **GOLDFISH 모드**(특수 키워드)

   ```yaml
   memorize_to: "GOLDFISH"
   ```

   완전한 메모리 리셋 — 대화 히스토리를 전혀 사용하지 않습니다.

3. **기본 동작**(`memorize_to`를 지정하지 않은 경우)

   ```yaml
   # memorize_to가 지정되지 않음 - 내부 ALL_INVOLVED 필터 사용
   ```

   해당 퍼슨이 발신자 또는 수신자인 메시지를 보여줍니다.

### 끝!

복잡한 enum도, 외워야 할 규칙 이름도 없습니다. 원하는 것을 자연어로 설명하거나, 메모리를 쓰지 않으려면 GOLDFISH만 사용하면 됩니다.

## 핵심 개념

### 전역 대화 모델

모든 메시지는 단일, 불변의 전역 대화에 저장됩니다:

```
┌─────────────────────────────┐
│   전역 대화(Global)         │
│ ┌─────────────────────────┐ │
│ │ Message 1: A → B        │ │
│ │ Message 2: B → A        │ │
│ │ Message 3: System → C   │ │
│ │ Message 4: C → A        │ │
│ │ ...                     │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

**특성:**

* **불변성**: 메시지는 삭제되지 않습니다.
* **공유성**: 모든 퍼슨이 동일한 대화에 접근합니다.
* **필터링**: 각 퍼슨은 메모리 설정에 따라 필터링된 뷰만 봅니다.

### 작업(Job) 단위 구성

메모리는 **퍼슨 단위가 아니라 작업 단위**로 구성합니다:

```yaml
nodes:
  - id: analyzer
    type: person_job
    person: alice
    memorize_to: "technical requirements, constraints"
    
  - id: summarizer
    type: person_job  
    person: alice  # 동일 퍼슨이지만, 다른 메모리!
    memorize_to: "key findings, conclusions"
    at_most: 5
```

## 동작 방식

### LLM 기반 선택 프로세스

자연어 기준을 지정하면:

1. **셀렉터 생성**: 시스템이 `{person_id}.__selector` 파셋을 생성
2. **지능형 분석**: 셀렉터가 모든 관련 메시지를 분석
3. **의미론적 이해**: 자연어 이해로 관련 콘텐츠 식별
4. **메시지 선택**: 가장 관련 있는 메시지 ID 반환
5. **작업 실행**: 기본 퍼슨이 선택된 메시지만으로 실행

### 구성 파라미터

```yaml
- label: "Technical Analysis"
  type: person_job
  props:
    person: Analyst
    memorize_to: "requirements, API design, performance constraints"
    at_most: 8  # 선택 메시지 최대 8개로 제한(옵션)
```

**파라미터:**

* `memorize_to`: 자연어 기준 또는 "GOLDFISH"
* `at_most`: 최대 메시지 수(옵션)

## 예시 패턴

### 1. 점진적 정련 파이프라인

```yaml
# 1단계: 광범위 분석
- label: Analyze
  type: person_job
  props:
    memorize_to: "user requirements, specifications, constraints"
    at_most: 30
    
# 2단계: 집중 요약
- label: Summarize  
  type: person_job
  props:
    memorize_to: "key decisions, analysis results"
    at_most: 15
    
# 3단계: 최종 추출
- label: Extract
  type: person_job
  props:
    memorize_to: "final conclusions, action items"
    at_most: 5
```

### 2. 멀티 에이전트 협업

```yaml
- label: Researcher
  type: person_job
  props:
    memorize_to: "research findings, data, evidence"
    at_most: 25
    
- label: Critic
  type: person_job
  props:
    memorize_to: "arguments, counterpoints, rebuttals"
    at_most: 10
    
- label: Moderator
  type: person_job
  props:
    # memorize_to 없음 - 본인이 관여한 모든 메시지를 봄
    at_most: 50
```

### 3. 새 출발 분석

```yaml
- label: "Unbiased Review"
  type: person_job
  props:
    person: Reviewer
    memorize_to: "GOLDFISH"  # 메모리 없음 - 편견 최소화
```

## 모범 사례

### 1. 자연어를 자유롭게 사용

LLM은 맥락과 의미를 이해합니다:

* ✅ `"requirements and constraints"`
* ✅ `"technical decisions, architecture choices"`
* ✅ `"user feedback, bug reports, feature requests"`
* ✅ `"everything about authentication and security"`

### 2. 합리적 한도 설정

* **무제한**: 포괄적 분석(`at_most` 생략)
* **20–30개**: 상세한 맥락
* **10–15개**: 집중 토론
* **3–5개**: 빠른 요약
* **0개**: `"GOLDFISH"` 사용

### 3. 인지 부하에 맞춘 메모리 설계

작업 복잡도에 맞추어 설정:

```yaml
# 복잡한 분석은 더 많은 컨텍스트 필요
memorize_to: "all technical discussions, decisions, trade-offs"
at_most: 40

# 단순 분류는 더 적게
memorize_to: "current request and its context"
at_most: 3
```

## 주요 이점

1. **단순성**: 평범한 영어(자연어)로 원하는 것을 설명하면 됨
2. **지능성**: LLM이 의미 기반 연관성을 이해
3. **유연성**: 동일 퍼슨도 작업마다 다른 메모리를 가짐
4. **효율성**: 관련 정보만 처리
5. **명확성**: 복잡한 enum이나 규칙이 필요 없음

## 흔한 사용 사례

### 기술 리뷰

```yaml
memorize_to: "code changes, review comments, technical debt"
```

### 고객 지원

```yaml
memorize_to: "customer issue, previous solutions, related tickets"
```

### 프로젝트 관리

```yaml
memorize_to: "deadlines, blockers, team decisions"
```

### 크리에이티브 라이팅

```yaml
memorize_to: "character development, plot points, themes"
```

## 메모리 적용 플로우

```
사용자 구성
       │
       ▼
"requirements, API design"  ──┐
                              │
       또는                   ├──→ MemorySelector.apply_memory_settings()
                              │
"GOLDFISH"  ──────────────────┘
       │
       ▼
   메모리 없음                   지능형 선택
                                        │
                                        ▼
                                 셀렉터 파셋 생성
                                        │
                                        ▼
                                 모든 메시지 분석
                                        │
                                        ▼
                                 관련 ID 선택
                                        │
                                        ▼
                                 메시지 필터링
                                        │
                                        ▼
                                 at_most 제한 적용
                                        │
                                        ▼
                                 필터링된 메모리로 실행
```

## 비파괴적(Non-Destructive) 메모리

DiPeO에서의 “잊기”는 비파괴적입니다:

* 원본 메시지는 전역 대화에 그대로 유지됩니다.
* 퍼슨의 뷰만 일시적으로 필터링됩니다.
* 메모리 설정 변경으로 언제든 되돌릴 수 있습니다.
* 항상 전체 감사 추적(audit trail)이 보존됩니다.

## 시스템 메시지 보존

`at_most` 제한을 사용할 때도 시스템 메시지는 자동으로 보존됩니다 — 별도 설정이 필요 없습니다. 이는 중요한 시스템 컨텍스트가 절대 손실되지 않도록 보장합니다.

---

## 내부 구현 세부사항

### 아키텍처 컴포넌트

메모리 시스템은 `MemorySelector` 클래스로 구현됩니다:

```python
from dipeo.application.execution.handlers.person_job.memory_selector import MemorySelector

# 메모리 설정 적용
selector = MemorySelector(orchestrator)
filtered_messages = await selector.apply_memory_settings(
    person=person,
    all_messages=all_messages,
    memorize_to="requirements, API design",
    at_most=10,
    task_prompt_preview=task_preview,
    llm_service=llm_service,
)
```

### 내부 필터 메서드

시스템은 다음의 내부 필터를 사용합니다(사용자에게 노출되지 않음):

* `_filter_all_involved()`: 퍼슨이 발신자 또는 수신자인 메시지(기본)
* `_filter_sent_by_me()`: 해당 퍼슨이 보낸 메시지만
* `_filter_sent_to_me()`: 해당 퍼슨에게 전송된 메시지만
* `_filter_system_and_me()`: 시스템 메시지와 퍼슨의 응답
* `_filter_conversation_pairs()`: 요청/응답 페어
* `_apply_limit()`: 메시지 수 제한 적용

이들은 기본 동작을 가능하게 하는 구현 디테일이며, 향후 확장의 토대가 됩니다.

### 셀렉터 파셋 상세

LLM 기반 선택의 경우:

* 파셋 ID: `{base_person_id}.__selector`
* 기본 퍼슨의 LLM 설정을 상속
* 특화된 선택 프롬프트를 추가
* 구조화된 목록으로 후보 메시지를 입력받음
* 메시지 ID의 JSON 배열을 반환
* 일관성을 위해 temperature는 0.1로 설정

### 메시지 ID 매핑

시스템은 선택을 위해 메시지 ID를 유지합니다:

1. 셀렉터가 ID가 포함된 메시지를 입력으로 받음
2. 선택된 ID를 JSON 배열로 반환
3. ID를 메시지 객체로 다시 매핑
4. 최종 필터링 및 제한 적용

## 향후 개선

1. **시간 기반 윈도우**: 최근 N분의 메시지 유지
2. **우선순위 보존**: 중요 메시지 항상 유지
3. **캐싱**: 반복 패턴에 대한 선택 결과 캐시
4. **하이브리드 선택**: 다중 선택 전략 결합
5. **컨텍스트 주입**: 외부 컨텍스트를 선택 기준에 추가

## 요약

DiPeO의 메모리 시스템은 자연어를 통한 직관적 제어를 제공합니다. 셀렉터 파셋 + 기본 퍼슨의 듀얼 퍼소나 접근은 복잡함 없이 지능형 메모리 관리를 가능하게 합니다. 사용자는 기억하고 싶은 것을 자연어로 설명하기만 하면, 시스템이 LLM 기반 이해를 통해 나머지를 처리합니다.

자연어 또는 GOLDFISH의 두 가지 옵션만으로도 의미 기반 선택의 모든 강점을 유지할 수 있습니다. “단순한 인터페이스, 지능적인 구현”이라는 설계 철학이 전체 메모리 시스템 아키텍처를 이끌고 있습니다.

```
