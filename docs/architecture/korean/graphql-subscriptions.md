# GraphQL 구독(Subscriptions) 구현 가이드

원문 문서:&#x20;

## 개요

DiPeO는 실시간 업데이트를 위해 GraphQL 구독만을 사용합니다. GraphQL 구독은 통합된 WebSocket 전송 메커니즘을 통해 모든 실시간 통신을 처리합니다. 이 가이드는 구독 시스템 아키텍처와 새로운 구독을 추가하는 방법을 설명합니다.&#x20;

### 사용 가능한 구독

1. **execution\_updates**: 실행 생애주기 이벤트를 위한 메인 구독

   * 실행 관련 모든 이벤트 처리(시작, 완료, 실패, 로그 등)
   * 프런트엔드 모니터링 및 로깅 컴포넌트에서 사용

2. **node\_updates**: 노드별 상태 업데이트

   * 개별 노드의 상태 변화와 진행 상황 추적
   * `node_id`로 선택적 필터링 가능

3. **interactive\_prompts**: 사용자 상호작용 요청

   * 실행 중 사용자 입력이 필요한 프롬프트 처리
   * `UserResponseNode` 및 인터랙티브 워크플로우에서 사용

4. **execution\_logs**: 전용 로그 스트리밍

   * `EXECUTION_LOG` 이벤트만을 대상으로 필터링
   * 로그 뷰어 컴포넌트에서 사용&#x20;

## 아키텍처

### 구성요소

1. **백엔드 구독 핸들러** (`/dipeo/application/graphql/schema/subscriptions.py`)

   * GraphQL 구독 엔드포인트 정의
   * 이벤트 분배를 위한 MessageRouter와 연결
   * JSON 호환 직렬화 수행
   * 현재 4개 구독 구현: `execution_updates`, `node_updates`, `interactive_prompts`, `execution_logs`

2. **이벤트 시스템** (`/dipeo/diagram_generated/enums.py`)

   * `EventType` enum이 모든 이벤트 타입 정의
   * 이벤트는 `AsyncEventBus`를 통해 발행
   * 예: `EXECUTION_STARTED`, `NODE_COMPLETED`, `NODE_STATUS_CHANGED`, `EXECUTION_LOG` 등

3. **메시지 라우터** (`/dipeo/infrastructure/adapters/messaging/message_router.py`)

   * 중앙 이벤트 분배 허브
   * 연결 라이프사이클 관리
   * 특징:

     * 이벤트 버퍼링(실행별 최근 50개, TTL 5분)
     * 성능을 위한 이벤트 배칭(주기/크기 구성 가능)
     * 연결 상태 모니터링
     * 유한 큐 기반의 백프레셔 처리

4. **프런트엔드 훅** (`/apps/web/src/domain/execution/hooks/`)

   * GraphQL 구독을 구독하는 React 훅
   * 수신 이벤트를 처리하고 UI 상태를 갱신
   * 예: 로그 스트리밍용 `useExecutionLogStream`&#x20;

## 새 구독 추가하기

### 1단계: 이벤트 타입 정의

TypeScript enum에 새 이벤트 타입 추가:

```typescript
// /dipeo/models/src/core/enums/execution.ts
export enum EventType {
  // ... existing events
  YOUR_NEW_EVENT = 'YOUR_NEW_EVENT'
}
```

백엔드 모델 재생성:

```bash
cd /dipeo/models && pnpm build
dipeo run codegen/diagrams/generate_all --light --debug
make apply-syntax-only
```

### 2단계: GraphQL 구독 생성

백엔드 스키마에 구독 추가:
```python
# /dipeo/application/graphql/schema/subscriptions.py
@strawberry.subscription
async def your_new_subscription(
    self, execution_id: strawberry.ID
) -> AsyncGenerator[JSONScalar, None]:
    """Subscribe to your new events."""
    message_router = registry.get(MESSAGE_ROUTER)
    
    if not message_router:
        logger.error("Message router not available")
        return
    
    exec_id = ExecutionID(str(execution_id))
    
    try:
        # Create event queue
        event_queue = asyncio.Queue()
        connection_id = f"graphql-your-subscription-{id(event_queue)}"
        
        # Define handler
        async def event_handler(message):
            serialized_message = serialize_for_json(message)
            await event_queue.put(serialized_message)
        
        # Register and subscribe
        await message_router.register_connection(connection_id, event_handler)
        await message_router.subscribe_connection_to_execution(connection_id, str(exec_id))
        
        try:
            # Yield events
            while True:
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                    # Filter for your event type
                    if event.get("type") == EventType.YOUR_NEW_EVENT.value:
                        yield serialize_for_json(event.get("data", {}))
                except asyncio.TimeoutError:
                    continue
        finally:
            # Clean up
            await message_router.unsubscribe_connection_from_execution(connection_id, str(exec_id))
            await message_router.unregister_connection(connection_id)
            
    except Exception as e:
        logger.error(f"Error in subscription: {e}")
        raise
```

### 3단계: 쿼리 정의에 구독 추가

해당 쿼리 정의 파일에 구독 추가:
```typescript
// /dipeo/models/src/frontend/query-definitions/executions.ts
// Add to executionQueries.queries array:
{
  name: 'YourNewSubscription',
  type: QueryOperationType.SUBSCRIPTION,
  variables: [
    { name: 'execution_id', type: 'ID', required: true }
  ],
  fields: [
    {
      name: 'your_new_subscription',
      args: [
        { name: 'execution_id', value: 'execution_id', isVariable: true }
      ],
      fields: [
        { name: 'field1' },
        { name: 'field2' },
        // ... subscription fields
      ]
    }
  ]
}
```

프런트엔드 쿼리 재생성:
```bash
# Build TypeScript models
cd dipeo/models && pnpm build

# Run code generation
dipeo run codegen/diagrams/generate_all --light --debug
make apply-syntax-only

# Update GraphQL schema and TypeScript types
make graphql-schema
```

### 4단계: 프런트엔드 훅 생성

구독을 위한 React 훅 생성:
```typescript
// /apps/web/src/domain/execution/hooks/useYourNewSubscription.ts
import { useState, useEffect } from 'react';
import { executionId } from '@/infrastructure/types';
import { useYourNewSubscriptionSubscription } from '@/__generated__/graphql';

export function useYourNewSubscription(executionIdParam: ReturnType<typeof executionId> | null) {
  const [data, setData] = useState<YourDataType[]>([]);

  const { data: subscriptionData } = useYourNewSubscriptionSubscription({
    variables: { executionId: executionIdParam || '' },
    skip: !executionIdParam,
  });

  useEffect(() => {
    if (subscriptionData?.your_new_subscription) {
      // Process incoming data
      const newData = subscriptionData.your_new_subscription;
      setData(prev => [...prev, newData]);
    }
  }, [subscriptionData]);

  return { data };
}
```

### 5단계: 이벤트 발행

`AsyncEventBus`를 사용하여 이벤트 발행:
```python
# In any handler or service
from dipeo.infrastructure.events.adapters.legacy import AsyncEventBus, Event

event_bus = AsyncEventBus.get_instance()
await event_bus.emit(Event(
    type=EventType.YOUR_NEW_EVENT,
    execution_id=execution_id,
    data={
        # Your event data
    }
))
```

MessageRouter는 이러한 이벤트를 자동으로 감지하고 구독된 연결로 분배합니다.

## 예시: ExecutionUpdates 구현

`ExecutionUpdates` 구독은 전체 구현 패턴을 보여줍니다:

1. **이벤트 타입**: `EXECUTION_STARTED`, `NODE_COMPLETED`, `EXECUTION_LOG` 등 다수 이벤트 처리
2. **GraphQL 구독**: `/dipeo/application/graphql/schema/subscriptions.py`의 `execution_updates`
3. **프런트엔드 쿼리 정의**: `/dipeo/models/src/frontend/query-definitions/executions.ts`에 정의
4. **생성된 쿼리**: `/apps/web/src/__generated__/queries/all-queries.ts`에 생성
5. **React 훅**: `useExecutionLogStream`이 `useExecutionUpdatesSubscription` 사용
6. **이벤트 발행**: `AsyncEventBus`가 발행하고 MessageRouter가 분배&#x20;

## 모범 사례

1. **이벤트 명명**: 이벤트 타입은 UPPER\_SNAKE\_CASE 사용
2. **데이터 직렬화**: 복잡한 객체는 항상 `serialize_for_json()` 사용
3. **에러 처리**: `try-catch`와 `finally`에서 정리 로직 포함
4. **타임아웃 처리**: 적절한 타임아웃으로 `asyncio.wait_for` 사용
5. **연결 정리**: 완료 시 항상 구독 해제 및 등록 해제 수행&#x20;

## 구독 테스트

### 백엔드 테스트

```python
# Test event emission via AsyncEventBus
from dipeo.infrastructure.events.adapters.legacy import AsyncEventBus, Event
from dipeo.diagram_generated.enums import EventType

event_bus = AsyncEventBus.get_instance()
await event_bus.emit(Event(
    type=EventType.EXECUTION_LOG,
    execution_id="test-exec-id",
    data={"message": "Test log", "level": "INFO"}
))

# Verify in logs that MessageRouter distributes the event
```

### 프런트엔드 테스트
```bash
# Run dev server with GraphQL playground
make dev-all

# Open GraphQL playground at http://localhost:8000/graphql
# Test subscription directly:
subscription {
  execution_updates(execution_id: "your-exec-id") {
    execution_id
    event_type
    data
    timestamp
  }
}

# Monitor WebSocket frames in browser DevTools Network tab
```

### CLI 테스트
```bash
# Run diagram with debug flag
dipeo run [diagram] --debug

# Monitor execution in web UI
# Open http://localhost:3000/?monitor=true
# Check console logs for subscription events
```

## 일반적인 이슈

### 이슈: 이벤트가 수신되지 않음
- MessageRouter 연결 등록 상태 확인  
- 이벤트 타입이 필터와 일치하는지 확인  
- `execution_id`가 올바른지 확인

### 이슈: 이벤트 중복 수신
- 중복 구독 여부 확인  
- 정리(cleanup)가 정상 동작하는지 확인  
- 동일 이벤트가 여러 번 발행되는지 확인

### 이슈: 메모리 누수
- `finally` 블록에서 적절한 정리 수행  
- 닫히지 않은 연결 확인  
- 큐 크기 모니터링

## 아키텍처 노트

### 현재 구현
시스템은 실시간 업데이트에 GraphQL 구독만을 사용합니다:  
- **전송**: Apollo Client 기반 GraphQL WebSocket  
- **백엔드**: 비동기 생성자를 사용하는 Strawberry GraphQL  
- **메시지 라우터**: 배칭/버퍼링을 갖춘 중앙 분배 허브  
- **타입 안정성**: GraphQL 스키마로부터 생성된 TypeScript 타입

### 멀티 워커 지원
프로덕션에서 멀티 워커를 사용할 경우:  
- 워커 간 구독 동작을 위해 Redis 필요  
- Redis가 없으면 단일 워커 배포에서만 구독 동작  
- 구성: 멀티 워커 지원을 위해 `REDIS_URL` 환경 변수 설정

### 이벤트 시스템 통합
- 이벤트는 `AsyncEventBus`를 통해 발행  
- `MessageRouter`가 이벤트를 구독하고 GraphQL 연결로 분배  
- 고빈도 업데이트를 위해 이벤트 배칭으로 성능 향상  
- 백프레셔 대응을 위해 유한 큐로 메모리 이슈 방지 

## 관련 문서

- DiPeO 애플리케이션 레이어 — GraphQL 스키마/리졸버 구현  
- 인프라 레이어 — MessageRouter와 이벤트 시스템 상세  
- 프런트엔드 아키텍처 — 구독 훅과 상태 관리  
- 코드 생성 — 쿼리/구독 생성 방법  
- DiPeO 모델 — TypeScript 쿼리 정의 소스

