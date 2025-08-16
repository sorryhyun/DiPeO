# DiPeO의 메모리 시스템 설계&#x20;

## 개요

DiPeO는 LLM 에이전트(“Person”)가 **공유 전역 대화**를 서로 다르게 바라볼 수 있도록 하는 정교한 메모리 관리 시스템을 구현합니다. 이 설계는 동일한 에이전트가 워크플로의 시점에 따라 서로 **다른 메모리 컨텍스트**를 갖도록 하여 강력한 워크플로 패턴을 가능하게 합니다.

## 핵심 개념

### 1. 전역 대화 모델

DiPeO 워크플로의 모든 메시지는 **단일 전역 대화**에 저장되며, 이것이 진실의 근원(source of truth)이 됩니다:

```
┌─────────────────────────────┐
│       전역 대화(Global)     │
│ ┌─────────────────────────┐ │
│ │ 메시지 1: A → B         │ │
│ │ 메시지 2: B → A         │ │
│ │ 메시지 3: System → C    │ │
│ │ 메시지 4: C → A         │ │
│ │ ...                     │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

**핵심 속성:**

* **불변(Immutable)**: 메시지는 삭제되지 않으며, 오직 필터링만 됩니다.
* **감사 가능(Auditable)**: 전체 이력이 항상 보존됩니다.
* **공유됨(Shared)**: 모든 person이 동일한 대화에 접근합니다.

### 2. 메모리 뷰(필터)

각 person은 전역 대화를 **구성 가능한 필터**를 통해 봅니다:

| View                 | 설명                         | 사용 사례            |
| -------------------- | -------------------------- | ---------------- |
| `ALL_INVOLVED`       | 해당 person이 발신자 또는 수신자인 메시지 | 일반 대화 참여         |
| `SENT_BY_ME`         | 이 person이 보낸 메시지만          | 자기 점검, 출력 검토     |
| `SENT_TO_ME`         | 이 person에게 보낸 메시지만         | 입력 처리, 분류        |
| `SYSTEM_AND_ME`      | 시스템 메시지와 person의 응답        | 작업 중심 실행         |
| `CONVERSATION_PAIRS` | 요청/응답 쌍                    | 토론, Q\&A 시나리오    |
| `ALL_MESSAGES`       | 대화의 모든 메시지                 | 코디네이터를 위한 완전 가시성 |

### 3. 메모리 한계(윈도우)

필터링 후, **슬라이딩 윈도우**로 메시지 수를 제한할 수 있습니다:

```python
# 예시: 필터된 뷰에서 마지막 10개 메시지만 보기
memory_settings = MemorySettings(
    view=MemoryView.ALL_INVOLVED,
    max_messages=10,
    preserve_system=True  # 시스템 메시지는 항상 유지
)
```

### 4. 작업(Job) 단위 구성

메모리 설정은 **person 수준이 아니라 작업(Job) 수준**에서 구성됩니다:

```yaml
nodes:
  - id: analyzer
    type: person_job
    person: alice
    memory_profile: FULL  # 모든 것을 봄
    
  - id: summarizer
    type: person_job  
    person: alice  # 같은 person!
    memory_profile: MINIMAL  # 제한된 컨텍스트(5개 메시지)
```

## 메모리 구성 문법

메모리 구성에는 두 가지 방법이 있습니다:

1. **메모리 프로파일(권장)** — 미리 정의된 구성:

```yaml
- label: PersonNode
  type: person_job
  props:
    memory_profile: FOCUSED  # 옵션: GOLDFISH, MINIMAL, FOCUSED, FULL, ONLY_ME, ONLY_I_SENT, CUSTOM
```

2. **사용자 지정 메모리 설정** — 세밀 제어(`memory_profile: CUSTOM`일 때 사용):

```yaml
- label: PersonNode
  type: person_job
  props:
    memory_profile: CUSTOM
    memory_settings:
      view: conversation_pairs
      max_messages: 10
      preserve_system: true
```

### 메모리 프로파일 정의

* **GOLDFISH**: 2개 메시지, conversation pairs 뷰(실행 간 완전 리셋)
* **MINIMAL**: 5개 메시지, conversation pairs 뷰
* **FOCUSED**: 20개 메시지, conversation pairs 뷰
* **FULL**: 제한 없음, all messages 뷰
* **ONLY\_ME**: 이 person에게 **보낸** 메시지만
* **ONLY\_I\_SENT**: 이 person이 **보낸** 메시지만
* **CUSTOM**: 명시적 `memory_settings` 사용

## 일반 패턴

### 1. 토론 패턴

참가자는 현재 교환에 집중하고, 심판(judge)은 전체 컨텍스트를 봅니다:

```yaml
- label: Optimist
  type: person_job
  props:
    memory_profile: FOCUSED  # 제한된 대화 컨텍스트
    max_iteration: 3

- label: Judge
  type: person_job
  props:
    memory_profile: FULL     # 전체를 조회
```

### 2. 파이프라인 패턴

컨텍스트를 점차 줄이며 정제하는 흐름:

```yaml
# 1단계: 전체 분석
- label: Analyze
  memory_profile: FULL
    
# 2단계: 집중 요약
- label: Summarize  
  memory_profile: FOCUSED   # 최근 교환에 집중
    
# 3단계: 최종 추출
- label: Extract
  memory_profile: MINIMAL   # 최신 소수 메시지만
```

### 3. 다중 에이전트 협업

같은 대화를 서로 다른 관점에서 보는 다양한 에이전트:

```yaml
persons:
  researcher:
    # 포괄적 분석을 위해 모든 메시지 참조
  critic:
    # 집중된 비평을 위해 대화 쌍에만 초점
  moderator:
    # 토론 관리를 위해 전체를 참조
```

## 구현 세부사항

### 메시지 라우팅

메시지가 대화에 추가되면:

1. 전역 대화에 저장됩니다.
2. 각 person의 필터에 따라 자동으로 포함/제외됩니다.
3. person별 중복 저장이 필요 없습니다.

### 메모리 적용 시점

선택한 프로파일에 따라 메모리 설정이 적용됩니다:

* **GOLDFISH**: 실행 간 완전 리셋(대화 이력 초기화)
* **그 외 프로파일**: 노드 초기화 시 적용되어 실행 내내 유지
* **사용자 지정 설정**: `memory_profile: CUSTOM`일 때 적용

### 비파괴적 망각(Non-Destructive Forgetting)

DiPeO에서의 “망각”은 **데이터 삭제가 아니라 가시성 제한**을 의미합니다:

* 원본 메시지는 전역 대화에 남아 있습니다.
* person의 뷰는 필터와 제한으로 축소됩니다.
* 설정 변경으로 언제든 되돌릴 수 있습니다.

## 모범 사례

### 1. 적절한 메모리 뷰 선택

* **토론/논증**: `conversation_pairs`로 교환에 집중
* **분석 작업**: `all_involved`로 충분한 컨텍스트 확보
* **분류/판별**: `sent_to_me`로 입력에만 집중
* **모니터링**: `system_and_me`로 작업 지시에만 초점

### 2. 합리적 한계 설정

* **무제한**: 심판, 분석자, 최종 검토자
* **10–20개**: 일반 대화 작업
* **1–5개**: 빠른 반응, 분류기
* **0개**: 완전 리셋(드묾)

### 3. 워크플로 흐름 고려

각 단계의 인지 요구에 맞게 메모리를 설계하세요:

```
전체 컨텍스트 → 필터된 컨텍스트 → 최소 컨텍스트 → 의사결정
```

### 4. 시스템 메시지 보존

대개 `preserve_system=True`로 지시를 유지합니다:

```yaml
memory_config:
  max_messages: 5
  preserve_system: true  # 시스템 프롬프트 유지
```

## 고급 구성

### 코드에서 메모리 프로파일 사용

시스템은 `MemoryProfileFactory`를 통해 사전 정의된 프로파일을 제공합니다:

```python
from dipeo.domain.conversation.memory_profiles import MemoryProfile, MemoryProfileFactory

# 프로파일의 설정 가져오기
settings = MemoryProfileFactory.get_settings(MemoryProfile.FOCUSED)
# 반환: MemorySettings(view=CONVERSATION_PAIRS, max_messages=20, preserve_system=True)
```

### 사용 가능한 메모리 프로파일

```python
class MemoryProfile(Enum):
    FULL = auto()        # 제한 없음, 모든 메시지
    FOCUSED = auto()     # 20개, conversation_pairs
    MINIMAL = auto()     # 5개, conversation_pairs  
    GOLDFISH = auto()    # 2개, conversation_pairs (리셋 포함)
    ONLY_ME = auto()     # person에게 보낸 메시지만
    ONLY_I_SENT = auto() # person이 보낸 메시지만
    CUSTOM = auto()      # 명시적 memory_settings 사용
```

### 동적 메모리 관리

보통 메모리는 작업 수준에서 설정하지만, 프로그램적으로 조정할 수도 있습니다:

```python
# person에 메모리 설정 적용
person.set_memory_view(MemoryView.CONVERSATION_PAIRS)
person.set_memory_limit(max_messages=10, preserve_system=True)
```

## 향후 개선

1. **의미 기반 필터링**: 메시지 내용/주제에 따른 필터
2. **시간 기반 윈도우**: 최근 N분의 메시지만 유지
3. **우선순위 보존**: 중요한 메시지는 한계와 무관하게 유지
4. **메모리 프로파일 확장**: 일반 패턴에 대한 추가 사전 설정

## 요약

DiPeO의 메모리 시스템은 **공유 전역 대화**에서 각 LLM 에이전트가 볼 수 있는 정보를 **작업 단위**로 유연하게 제어합니다. 이를 통해 단순성과 감사 가능성을 유지하면서도 정교한 **멀티에이전트 워크플로**를 구성할 수 있습니다. 핵심 통찰은 **메모리 구성이 person(에이전트) 단위가 아니라 job(작업) 단위**에 속한다는 점이며, 같은 에이전트라도 작업에 따라 서로 다른 메모리 컨텍스트를 가질 수 있다는 것입니다.&#x20;
