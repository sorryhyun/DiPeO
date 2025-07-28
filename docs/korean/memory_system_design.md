# DiPeO의 메모리 시스템 설계

## 개요

DiPeO는 LLM 에이전트(Persons)가 공유된 전역 대화에 대해 서로 다른 뷰를 가질 수 있도록 하는 정교한 메모리 관리 시스템을 구현합니다. 이 설계를 통해 동일한 에이전트가 워크플로우의 다른 지점에서 다른 메모리 컨텍스트를 가질 수 있는 강력한 워크플로우 패턴이 가능해집니다.

## 핵심 개념

### 1. 전역 대화 모델

DiPeO 워크플로우의 모든 메시지는 진실의 원천(source of truth) 역할을 하는 단일 전역 대화에 저장됩니다:

```
┌─────────────────────────────┐
│   Global Conversation       │
│ ┌─────────────────────────┐ │
│ │ Message 1: A → B        │ │
│ │ Message 2: B → A        │ │
│ │ Message 3: System → C   │ │
│ │ Message 4: C → A        │ │
│ │ ...                     │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

**주요 특성:**
- **불변성**: 메시지는 삭제되지 않고 필터링만 됨
- **감사 가능**: 전체 히스토리가 항상 보존됨
- **공유됨**: 모든 person이 동일한 대화에 접근

### 2. 메모리 뷰 (필터)

각 person은 구성 가능한 필터를 통해 전역 대화를 봅니다:

| 뷰 | 설명 | 사용 사례 |
|------|-------------|----------|
| `ALL_INVOLVED` | person이 발신자 또는 수신자인 메시지 | 일반 대화 참여자 |
| `SENT_BY_ME` | 이 person이 보낸 메시지만 | 자기 성찰, 출력 검토 |
| `SENT_TO_ME` | 이 person에게 보낸 메시지만 | 입력 처리, 분류 |
| `SYSTEM_AND_ME` | 시스템 메시지와 person의 응답 | 작업 중심 실행 |
| `CONVERSATION_PAIRS` | 요청/응답 쌍 | 토론, Q&A 시나리오 |

### 3. 메모리 제한 (윈도우)

필터링 후 슬라이딩 윈도우로 메시지 수를 제한할 수 있습니다:

```python
# 예시: 필터링된 뷰에서 마지막 10개 메시지만 보기
memory_settings = MemorySettings(
    view=MemoryView.ALL_INVOLVED,
    max_messages=10,
    preserve_system=True  # 시스템 메시지는 항상 유지
)
```

### 4. 작업별 구성

메모리 설정은 person 레벨이 아닌 **작업(job) 레벨**에서 구성됩니다:

```yaml
nodes:
  - id: analyzer
    type: person_job
    person: alice
    memory_config:
      forget_mode: no_forget  # 모든 것을 봄
    
  - id: summarizer
    type: person_job  
    person: alice  # 동일한 person!
    memory_config:
      forget_mode: on_every_turn  # 제한된 컨텍스트
      max_messages: 5
```

## 메모리 구성 문법

`memory_config` 문법은 계속 작동합니다:

```yaml
- label: PersonNode
  type: person_job
  props:
    memory_config:
      forget_mode: on_every_turn
      max_messages: 10
```

## 일반적인 패턴

### 1. 토론 패턴

참가자들은 현재 교환에 집중하고 심사위원은 전체 컨텍스트가 필요합니다:

```yaml
- label: Optimist
  type: person_job
  props:
    memory_config:
      forget_mode: on_every_turn  # Q&A 쌍을 봄
    max_iteration: 3

- label: Judge
  type: person_job
  props:
    memory_config:
      forget_mode: no_forget       # 모든 것을 봄
```

### 2. 파이프라인 패턴

컨텍스트를 줄여가며 점진적으로 개선:

```yaml
# Stage 1: 전체 분석
- label: Analyze
  memory_config:
    forget_mode: no_forget
    
# Stage 2: 집중된 요약
- label: Summarize  
  memory_config:
    forget_mode: on_every_turn   # 교환에 집중
    
# Stage 3: 최종 추출
- label: Extract
  memory_config:
    forget_mode: upon_request          # 직접 입력만
```

### 3. 다중 에이전트 협업

동일한 대화에 대해 다른 관점을 가진 다른 에이전트들:

```yaml
persons:
  researcher:
    # 포괄적인 분석을 위해 모든 메시지를 봄
  critic:
    # 집중된 비평을 위해 대화 쌍만 봄
  moderator:
    # 토론을 관리하기 위해 모든 메시지를 봄
```

## 구현 세부사항

### 메시지 라우팅

메시지가 대화에 추가될 때:
1. 전역 대화에 저장됨
2. 각 person의 뷰는 필터에 따라 자동으로 포함/제외
3. 중복이나 person별 저장이 필요 없음

### 메모리 적용 타이밍

노드 핸들러가 메모리 설정을 적용할 시기를 결정:
- `on_every_turn`: `execution_count > 0`일 때 적용
- `upon_request`: 명시적으로 트리거될 때 적용
- `no_forget`: 메모리 관리가 적용되지 않음

### 비파괴적 망각

DiPeO에서 "망각"은 데이터 삭제가 아닌 person이 볼 수 있는 것을 제한하는 것을 의미:
- 원본 메시지는 전역 대화에 남아 있음
- Person의 뷰가 필터와 제한을 통해 제한됨
- 메모리 설정을 변경하여 되돌릴 수 있음

## 모범 사례

### 1. 적절한 메모리 뷰 선택

- **토론/논쟁**: 교환에 집중하기 위해 `conversation_pairs` 사용
- **분석 작업**: 전체 컨텍스트를 위해 `all_involved` 사용
- **분류**: 입력만을 위해 `sent_to_me` 사용
- **모니터링**: 작업별 메시지를 위해 `system_and_me` 사용

### 2. 합리적인 제한 설정

- **제한 없음**: 심사위원, 분석가, 최종 검토자
- **10-20개 메시지**: 일반 대화 작업
- **1-5개 메시지**: 빠른 반응, 분류기
- **0개 메시지**: 완전한 재설정 (드물게 사용)

### 3. 워크플로우 흐름 고려

각 단계의 인지적 요구사항에 맞는 메모리 설정 설계:
```
전체 컨텍스트 → 필터링된 컨텍스트 → 최소 컨텍스트 → 결정
```

### 4. 시스템 메시지 보존

작업 지시사항을 유지하기 위해 보통 `preserve_system=True` 유지:
```yaml
memory_config:
  max_messages: 5
  preserve_system: true  # 시스템 프롬프트 유지
```

## 고급 구성

### 사용자 정의 메모리 프로필

재사용 가능한 메모리 구성 생성:

```python
MEMORY_PROFILES = {
    "ANALYST": MemorySettings(view=ALL_INVOLVED, max_messages=None),
    "DEBATER": MemorySettings(view=CONVERSATION_PAIRS, max_messages=4),
    "CLASSIFIER": MemorySettings(view=SENT_TO_ME, max_messages=1),
    "GOLDFISH": MemorySettings(view=CONVERSATION_PAIRS, max_messages=2),
}
```

### 동적 메모리 관리

실행 상태에 따라 메모리 조정:

```python
if execution_count > 10:
    # 많은 반복 후 컨텍스트 축소
    person.apply_memory_settings(
        MemorySettings(max_messages=5)
    )
```

## 향후 개선사항

1. **의미론적 필터링**: 메시지 내용/주제별 필터링
2. **시간 기반 윈도우**: 최근 N분간의 메시지 유지
3. **우선순위 보존**: 제한에 관계없이 중요한 메시지 유지
4. **메모리 프로필**: 일반적인 패턴을 위한 사전 정의된 구성

## 요약

DiPeO의 메모리 시스템은 공유된 전역 대화에서 각 LLM 에이전트가 볼 수 있는 것에 대한 유연한 작업별 제어를 제공합니다. 이를 통해 단순성과 감사 가능성을 유지하면서도 정교한 다중 에이전트 워크플로우가 가능해집니다. 핵심 통찰은 메모리 구성이 person(에이전트)이 아닌 작업(job)에 속한다는 것으로, 동일한 에이전트가 워크플로우의 다른 작업에 대해 다른 메모리 컨텍스트를 가질 수 있게 합니다.