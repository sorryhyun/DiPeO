# 코드 생성 가이드

## 개요

DiPeO는 TypeScript 노드 명세에서 GraphQL 쿼리와 Python 핸들러까지 타입 안전성을 유지하기 위해 다단계 코드 생성 파이프라인을 사용합니다.

## 생성 흐름

```
1. 노드 명세 (TypeScript)
   ↓
2. 도메인 모델 생성 → /dipeo/diagram_generated_staged/
   ↓
3. 백엔드 코드 생성
   ↓
4. 스테이징된 변경사항 적용 (make apply)
   ↓
5. 프론트엔드 코드 생성 (적용된 모델에 의존)
   ↓
6. GraphQL 스키마 내보내기 (make graphql-schema)
```

**중요**: 코드 생성 프로세스는 스테이징 디렉토리(`/dipeo/diagram_generated_staged/`)를 사용하여 도메인 모델 변경사항을 적용하기 전에 미리 확인합니다. 이를 통해 프론트엔드 생성이 최신 도메인 모델을 볼 수 있도록 보장합니다.

### 단계 1: 노드 명세 → Python 모델

**소스**: `/dipeo/models/src/node-specs/*.spec.ts`  
**스테이징 출력**: `/dipeo/diagram_generated_staged/`  
**최종 출력**: `/dipeo/diagram_generated/`  
**명령어**: 
```bash
make codegen  # apply를 포함한 전체 파이프라인 실행
# 또는 수동으로:
dipeo run codegen/diagrams/models/generate_all_models --light --debug
make apply    # 스테이징된 변경사항 적용
```

생성되는 항목:
- Pydantic 모델 (`/models/`)
- JSON 스키마 (`/schemas/`)
- 검증 모델 (`/validation/`)
- 노드 구성 (`/nodes/`)

### 단계 2: 백엔드 코드 생성

**소스**: TypeScript 노드 명세  
**출력**: Python 노드 핸들러 및 구성  
**명령어**: `make codegen` 파이프라인의 일부

각 노드 타입에 대한 백엔드 전용 파일을 생성합니다.

### 단계 3: 스테이징된 변경사항 적용

**명령어**: `make apply`  
**동작**: `/dipeo/diagram_generated_staged/` → `/dipeo/diagram_generated/`로 복사

이 중요한 단계는 다음을 보장합니다:
- 프론트엔드 생성이 최신 도메인 모델을 확인
- 모든 컴포넌트가 일관된 타입 정의 사용
- 적용 전에 변경사항 검토 가능

### 단계 4: 프론트엔드 코드 생성

**소스**: 적용된 도메인 모델 + TypeScript 명세  
**출력**: 
- `/apps/web/src/__generated__/queries/*.graphql` - GraphQL 쿼리
- 프론트엔드 노드 구성 및 컴포넌트

생성되는 항목:
- `diagrams.graphql` - 다이어그램 CRUD 작업
- `persons.graphql` - 사용자 관리
- `executions.graphql` - 실행 모니터링
- 노드별 UI 컴포넌트 및 구성

### 단계 5: GraphQL 스키마 내보내기

**명령어**: `make graphql-schema`  
**출력**: `/apps/server/schema.graphql`

실행 중인 서버에서 전체 GraphQL 스키마를 내보내며, 다음을 보장합니다:
- 스키마가 모든 현재 타입과 작업을 반영
- 프론트엔드 코드젠이 최신 스키마 보유
- 문서가 동기화 상태 유지

### 단계 6: GraphQL TypeScript 생성

**소스**: `/apps/web/src/__generated__/queries/*.graphql` + `/apps/server/schema.graphql`  
**출력**: `/apps/web/src/__generated__/graphql.tsx`  
**명령어**: `pnpm codegen` (apps/web에서)

생성되는 항목:
- 모든 GraphQL 작업에 대한 TypeScript 타입
- React 훅 (useQuery, useMutation, useSubscription)
- Apollo Client 통합 코드

## 새로운 기능 추가하기

### 새 노드 타입 추가

1. **노드 명세 생성**:
   ```typescript
   // /dipeo/models/src/node-specs/my-node.spec.ts
   export const myNodeSpec: NodeSpecification = {
     nodeType: NodeType.MyNode,
     category: 'processing',
     fields: [
       {
         name: 'myField',
         type: 'string',
         required: true,
         description: '필드에 대한 설명'
       }
     ]
   };
   ```

2. **Python 핸들러 생성**:
   ```python
   # /dipeo/application/execution/handlers/my_node.py
   from dipeo.diagram_generated.models.my_node import MyNodeData
   
   class MyNodeHandler(BaseNodeHandler[MyNodeData]):
       async def execute(self, data: MyNodeData, context: ExecutionContext):
           # 구현
   ```

3. **코드 생성 실행**:
   ```bash
   make codegen
   ```

4. **노드가 이제 다이어그램 편집기에서** 완전한 타입 안전성과 함께 사용 가능합니다.

### 새 GraphQL 쿼리/뮤테이션 추가

1. **기존 엔티티의 경우**, 쿼리 생성기 수정:
   ```python
   # /projects/codegen/code/frontend/generators/query_generator_dipeo.py
   # generate_diagram_queries() 또는 유사한 메서드에서
   
   queries.append("""query MyNewQuery($id: ID!) {
     diagram(id: $id) {
       # 필드 추가
     }
   }""")
   ```

2. **새 엔티티의 경우**, 새 쿼리 생성기 생성:
   ```python
   # /projects/codegen/code/frontend/queries/my_entity_queries.py
   class MyEntityQueryGenerator:
       def generate(self) -> List[str]:
           return [
               """query GetMyEntity($id: ID!) {
                 myEntity(id: $id) {
                   id
                   name
                 }
               }"""
           ]
   ```

3. **메인 생성기에 등록**:
   ```python
   # DiPeOQueryGenerator.generate_all_queries()에서
   my_entity_generator = MyEntityQueryGenerator()
   self.write_query_file('myEntity', my_entity_generator.generate())
   ```

4. **생성 실행**:
   ```bash
   make codegen                 # 스키마 내보내기를 포함한 전체 파이프라인
   cd apps/web && pnpm codegen  # 업데이트된 스키마에서 TypeScript 생성
   ```

### 새 뮤테이션 추가

1. **스키마에 추가** (`/apps/server/schema.graphql`):
   ```graphql
   type Mutation {
     myNewMutation(input: MyInput!): MyResult!
   }
   ```

2. **쿼리 생성기에 추가**:
   ```python
   queries.append("""mutation MyNewMutation($input: MyInput!) {
     myNewMutation(input: $input) {
       success
       data {
         id
       }
       error
     }
   }""")
   ```

3. **리졸버 구현** `/dipeo/application/graphql/`에서:
   ```python
   @strawberry.mutation
   async def my_new_mutation(self, input: MyInput) -> MyResult:
       # 구현
   ```

## 주요 파일

### 코드 생성
- `/dipeo/models/src/node-specs/` - 노드 명세 (진실의 원천)
- `/projects/codegen/code/frontend/generators/` - 쿼리 생성기
- `/projects/codegen/diagrams/` - 코드젠 오케스트레이션 다이어그램

### 생성된 파일 (편집 금지)
- `/dipeo/diagram_generated/` - Python 모델 및 스키마
- `/apps/web/src/__generated__/queries/` - GraphQL 쿼리 정의
- `/apps/web/src/__generated__/graphql.tsx` - TypeScript 타입 및 훅

### 구성
- `/apps/web/codegen.yml` - GraphQL 코드 생성기 설정
- `/dipeo/models/tsconfig.json` - TypeScript에서 JSON Schema로 변환 설정

## 이 순서가 중요한 이유

`make apply`를 사용한 스테이징 접근법이 중요한 이유:
1. **도메인 모델이 먼저 생성되어야 함** - 핵심 타입을 정의
2. **도메인 모델 이후 백엔드 생성은 독립적으로 진행 가능**
3. **프론트엔드 전에 apply가 실행되어야 함** - 프론트엔드 쿼리는 실제 도메인 모델 파일에 의존
4. **프론트엔드 생성은 적용된 모델에서 읽음** - 스테이징 디렉토리가 아님
5. **모든 생성 후 GraphQL 스키마 내보내기 필요** - 모든 새 타입과 작업 캡처
6. **프론트엔드 TypeScript 생성은 내보낸 스키마에 의존** - 타입 일관성 보장

## 모범 사례

1. **생성된 파일을 절대 편집하지 마세요** - 덮어쓰여집니다
2. **명세 변경 후 `make codegen` 실행** - 전체 파이프라인을 자동으로 처리
3. **`make diff-staged`로 변경사항 미리보기** - 적용 전 검토
4. **필요할 때만 `make apply` 수동 실행** - 전체 코드젠에 포함됨
5. **타입이 지정된 작업 사용** - 프론트엔드에서 생성된 훅 활용
6. **명명 규칙 준수**:
   - 쿼리: `Get{Entity}`, `List{Entities}`
   - 뮤테이션: `Create{Entity}`, `Update{Entity}`, `Delete{Entity}`
   - 구독: `{Entity}Updates`

## 문제 해결

**노드 추가 후 타입 누락**:
```bash
make codegen  # 모든 것 재생성
make dev-all  # 서버 재시작
```

**GraphQL 쿼리를 찾을 수 없음**:
1. `/apps/web/src/__generated__/queries/`에 쿼리 파일이 생성되었는지 확인
2. `/apps/web/`에서 `pnpm codegen`이 실행되었는지 확인
3. 컴포넌트에서 쿼리 이름이 일치하는지 확인

**타입 불일치 오류**:
- 스키마와 쿼리가 동기화되지 않았을 수 있음
- `make codegen` 실행 후 `cd apps/web && pnpm codegen` 실행

## 아키텍처 노트

2단계 GraphQL 생성(Python이 쿼리 생성, 그다음 GraphQL 코드젠이 TypeScript 생성)은 다음을 제공합니다:
- **도메인 주도 쿼리**: 작업이 도메인 모델과 일치
- **타입 안전성**: Python에서 TypeScript까지 엔드투엔드  
- **유연성**: 스키마 변경 없이 쿼리 커스터마이징 가능
- **일관성**: 모든 쿼리가 동일한 패턴 따름

디렉토리 구조(`__generated__/queries/`)가 혼란스러워 보일 수 있지만, 이 쿼리 파일들은 GraphQL 코드 생성기의 소스 파일이지 출력물이 아닙니다. `graphql.tsx`만이 진정으로 생성된 파일입니다.