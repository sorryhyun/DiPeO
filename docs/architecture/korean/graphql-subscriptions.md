# GraphQL 구독(Subscriptions) 구현 가이드

## 개요

DiPeO는 실시간 업데이트를 **오직 GraphQL 구독**으로 처리합니다. 단일 WebSocket 전송 메커니즘 위에서 모든 실시간 메시지를 주고받으며, 이 문서는 구독 시스템의 아키텍처와 새로운 구독을 추가하는 방법을 설명합니다.

### 사용 가능한 구독

1. **execution_updates**: 실행 생애주기 이벤트를 위한 기본 구독입니다.
   - 실행 시작, 완료, 실패, 로그 등 모든 실행 이벤트를 전달합니다.
   - 프런트엔드 모니터링, 로그 스트리밍, 인터랙티브 컴포넌트에서 사용됩니다.
   - 현재 TypeScript 정의에서 생성되는 **유일한** 구독입니다.

**참고**: 인프라는 여러 구독 타입을 지원하지만, 기본 제공되는 생성 파이프라인은 `execution_updates` 하나만 생성합니다. 다른 구독을 사용하려면 쿼리 정의를 확장하고 코드 생성을 다시 실행해야 합니다.

## 아키텍처

### 구성요소

1. **백엔드 구독 핸들러** (`/dipeo/application/graphql/schema/subscription_resolvers.py`)
   - GraphQL 구독 엔드포인트를 정의합니다.
   - 이벤트 분배를 위해 MessageRouter와 연결됩니다.
   - JSON 직렬화를 담당합니다.
   - 현재 TypeScript로부터 생성된 구독은 `execution_updates` 하나입니다.

2. **이벤트 시스템** (`/dipeo/diagram_generated/enums.py`)
   - `EventType` enum이 모든 이벤트 타입을 정의합니다.
   - 이벤트는 `AsyncEventBus`를 통해 발행됩니다.
   - 예: `EXECUTION_STARTED`, `NODE_COMPLETED`, `NODE_STATUS_CHANGED`, `EXECUTION_LOG` 등.

3. **메시지 라우터** (`/dipeo/infrastructure/adapters/messaging/message_router.py`)
   - 중앙 메시지 분배 허브입니다.
   - 연결 수명 주기를 관리합니다.
   - 특징:
     - 실행별 최근 50개 이벤트를 5분 동안 버퍼링합니다.
     - 구성 가능한 주기·크기로 이벤트를 배치 처리합니다.
     - 연결 상태를 모니터링합니다.
     - 유한 큐 기반으로 백프레셔를 제어합니다.

4. **프런트엔드 훅** (`/apps/web/src/domain/execution/hooks/`)
   - GraphQL 구독을 사용하는 React 훅을 제공합니다.
   - 수신 이벤트를 처리해 UI 상태를 갱신합니다.
   - 예: 로그 스트리밍용 `useExecutionLogStream`.

## 새 구독 추가하기

### 1단계: 이벤트 타입 정의

TypeScript enum에 새 이벤트 타입을 추가합니다.

```typescript
// /dipeo/models/src/core/enums/execution.ts
export enum EventType {
  // ... existing events
  YOUR_NEW_EVENT = 'YOUR_NEW_EVENT'
}
```

백엔드 모델을 다시 생성합니다.

```bash
cd /dipeo/models && pnpm build
dipeo run codegen/diagrams/generate_all --light --debug
make apply-test
```

### 2단계: GraphQL 구독 생성

백엔드 스키마에 새 구독을 추가합니다.

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

해당 쿼리 정의 파일에 새 구독을 추가합니다.

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

프런트엔드 쿼리를 다시 생성합니다.

```bash
# Build TypeScript models
cd dipeo/models && pnpm build

# Run code generation
dipeo run codegen/diagrams/generate_all --light --debug
make apply-test

# Update GraphQL schema and TypeScript types
make graphql-schema
```

### 4단계: 프런트엔드 훅 생성

React 훅을 만들어 구독을 소비합니다.

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

`AsyncEventBus`를 통해 이벤트를 발행합니다.

```python
# In any handler or service
from dipeo.core.events import AsyncEventBus, Event

event_bus = AsyncEventBus.get_instance()
await event_bus.emit(Event(
    type=EventType.YOUR_NEW_EVENT,
    execution_id=execution_id,
    data={
        # Your event data
    }
))
```

MessageRouter는 이 이벤트를 자동으로 감지해 구독된 연결로 전달합니다.

## 예시: ExecutionUpdates 구현

`execution_updates` 구독은 전체 구현 패턴을 보여 줍니다.

1. **이벤트 타입**: `EXECUTION_STARTED`, `NODE_COMPLETED`, `EXECUTION_LOG` 등 여러 이벤트를 처리합니다.
2. **GraphQL 구독**: `/dipeo/application/graphql/schema/subscriptions.py`의 `execution_updates` 정의를 사용합니다.
3. **프런트엔드 쿼리 정의**: `/dipeo/models/src/frontend/query-definitions/executions.ts`에 선언되어 있습니다.
4. **생성된 쿼리**: `/apps/web/src/__generated__/queries/all-queries.ts`에서 생성됩니다.
5. **React 훅**: `useExecutionLogStream` 훅이 `useExecutionUpdatesSubscription`을 사용합니다.
6. **이벤트 발행**: `AsyncEventBus`가 이벤트를 발행하고 MessageRouter가 이를 분배합니다.

## 모범 사례

1. **이벤트 명명**: 이벤트 타입은 항상 `UPPER_SNAKE_CASE`를 사용합니다.
2. **데이터 직렬화**: 복잡한 객체는 반드시 `serialize_for_json()`으로 직렬화합니다.
3. **에러 처리**: `try/except`와 `finally`를 사용해 정리(cleanup)를 보장합니다.
4. **타임아웃 처리**: 적절한 시간으로 `asyncio.wait_for`를 사용합니다.
5. **연결 정리**: 구독이 종료되면 항상 구독 해제 및 등록 해제를 수행합니다.

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

### 이벤트가 수신되지 않을 때
- MessageRouter에 연결이 정상 등록되었는지 확인합니다.
- 이벤트 타입이 필터 조건과 일치하는지 확인합니다.
- `execution_id`가 올바른지 검증합니다.

### 이벤트가 중복 수신될 때
- 동일 구독이 여러 번 생성됐는지 확인합니다.
- 정리 로직이 제대로 실행되는지 확인합니다.
- 이벤트가 여러 번 발행되고 있지 않은지 점검합니다.

### 메모리 누수가 의심될 때
- `finally` 블록에서 구독 해제·등록 해제를 수행했는지 확인합니다.
- 닫히지 않은 연결이 있는지 점검합니다.
- 큐 크기를 모니터링합니다.

## 아키텍처 노트

### 현재 구현
- **전송**: Apollo Client 기반 GraphQL WebSocket 전송을 사용합니다.
- **백엔드**: Strawberry GraphQL과 비동기 제너레이터를 사용합니다.
- **메시지 라우터**: 배칭·버퍼링 기능을 갖춘 중앙 분배 허브입니다.
- **타입 안전성**: GraphQL 스키마에서 생성된 TypeScript 타입을 사용합니다.

### 멀티 워커 지원
- 프로덕션에서 여러 워커를 사용할 경우 Redis가 필요합니다.
- Redis가 없으면 단일 워커에서만 구독이 동작합니다.
- 다중 워커 구성 시 `REDIS_URL` 환경 변수를 설정해야 합니다.

### 이벤트 시스템 통합
- 이벤트는 `AsyncEventBus`를 통해 발행됩니다.
- `MessageRouter`가 이벤트를 구독하고 GraphQL 연결로 전달합니다.
- 고주파 이벤트의 경우 배칭이 성능을 향상시킵니다.
- 유한 큐로 백프레셔를 제어해 메모리 문제를 방지합니다.

## 관련 문서

- `../../dipeo/application/CLAUDE.md` – GraphQL 스키마와 리졸버 구현
- `../../dipeo/infrastructure/CLAUDE.md` – MessageRouter와 이벤트 시스템 상세
- `../../apps/web/CLAUDE.md` – 프런트엔드 구독 훅과 상태 관리
- `../../projects/codegen/CLAUDE.md` – 쿼리·구독 생성 파이프라인
- `../../dipeo/models/CLAUDE.md` – TypeScript 쿼리 정의의 소스
